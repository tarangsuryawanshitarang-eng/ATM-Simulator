"""
Banking Transaction Domain Service for the Advanced ATM Simulator.
Orchestrates atomic balance transitions, physical note dispensing, deposits, and mini-statements.
"""

from typing import Any, Dict, List, Optional

import config
from core.domain.transaction import TransactionRecord
from core.exceptions import (
    AccountLockedException,
    AccountNotFoundException,
    AtmBaseException,
    DatabaseTransactionError,
    InsufficientFundsException,
    InvalidAmountException,
    UnsupportedDenominationException,
)
from core.interfaces.repositories import IAccountRepository, ITransactionRepository
from core.interfaces.security import IHashProvider
from core.interfaces.transaction import ITransactionService, IVaultManagerService
from core.services.security import Pbkdf2PepperHashProvider


class BankingTransactionService(ITransactionService):
    """
    Concrete service managing banking operations for cardholders.
    """

    def __init__(
        self,
        account_repo: IAccountRepository,
        transaction_repo: ITransactionRepository,
        vault_service: IVaultManagerService,
        hash_provider: Optional[IHashProvider] = None,
    ):
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo
        self.vault_service = vault_service
        self.hash_provider = hash_provider or Pbkdf2PepperHashProvider()

    def check_balance(self, account_number: str) -> float:
        account = self.account_repo.get_by_number(account_number)
        if account is None:
            raise AccountNotFoundException(f"Account '{account_number}' not found.")

        if account.is_locked:
            self.transaction_repo.record_transaction(
                TransactionRecord(
                    account_number=account_number,
                    transaction_type="BALANCE_INQUIRY",
                    amount=0.0,
                    status="REJECTED",
                    failure_reason="ACCOUNT_LOCKED",
                )
            )
            raise AccountLockedException(f"Account '{account_number}' is locked.")

        self.transaction_repo.record_transaction(
            TransactionRecord(
                account_number=account_number,
                transaction_type="BALANCE_INQUIRY",
                amount=account.balance,
                status="SUCCESS",
                failure_reason=None,
            )
        )
        return account.balance

    def withdraw_cash(self, account_number: str, amount: float) -> Dict[str, Any]:
        account = self.account_repo.get_by_number(account_number)
        if account is None:
            raise AccountNotFoundException(f"Account '{account_number}' not found.")

        if account.is_locked:
            self.transaction_repo.record_transaction(
                TransactionRecord(
                    account_number=account_number,
                    transaction_type="WITHDRAWAL",
                    amount=amount,
                    status="REJECTED",
                    failure_reason="ACCOUNT_LOCKED",
                )
            )
            raise AccountLockedException(f"Account '{account_number}' is locked.")

        if amount <= 0:
            raise InvalidAmountException("Withdrawal amount must be greater than zero.")

        if account.balance < amount:
            self.transaction_repo.record_transaction(
                TransactionRecord(
                    account_number=account_number,
                    transaction_type="WITHDRAWAL",
                    amount=amount,
                    status="FAILED",
                    failure_reason="INSUFFICIENT_FUNDS",
                )
            )
            raise InsufficientFundsException(
                f"Insufficient funds. Balance: ${account.balance:.2f}, Requested: ${amount:.2f}."
            )

        try:
            # Dispense notes from physical cassette inventory
            dispensed_notes = self.vault_service.dispense(int(amount))

            # Deduct balance from account entity and persist
            new_balance = account.apply_withdrawal(amount)
            self.account_repo.save(account)

            tx_id = self.transaction_repo.record_transaction(
                TransactionRecord(
                    account_number=account_number,
                    transaction_type="WITHDRAWAL",
                    amount=amount,
                    status="SUCCESS",
                    failure_reason=None,
                )
            )

            return {
                "transaction_id": tx_id,
                "account_number": account_number,
                "amount": amount,
                "dispensed_notes": dispensed_notes,
                "new_balance": new_balance,
            }
        except AtmBaseException as e:
            self.transaction_repo.record_transaction(
                TransactionRecord(
                    account_number=account_number,
                    transaction_type="WITHDRAWAL",
                    amount=amount,
                    status="FAILED",
                    failure_reason=e.failure_reason,
                )
            )
            raise e

    def deposit_cash(self, account_number: str, amount_or_notes: Any) -> Dict[str, Any]:
        account = self.account_repo.get_by_number(account_number)
        if account is None:
            raise AccountNotFoundException(f"Account '{account_number}' not found.")

        if account.is_locked:
            self.transaction_repo.record_transaction(
                TransactionRecord(
                    account_number=account_number,
                    transaction_type="DEPOSIT",
                    amount=0.0,
                    status="REJECTED",
                    failure_reason="ACCOUNT_LOCKED",
                )
            )
            raise AccountLockedException(f"Account '{account_number}' is locked.")

        # Handle numeric monetary amount vs note breakdown
        if isinstance(amount_or_notes, (int, float)):
            amount_val = float(amount_or_notes)
            if amount_val <= 0:
                raise InvalidAmountException("Deposit amount must be greater than zero.")
            if amount_val % 100 != 0:
                raise UnsupportedDenominationException("Deposit amount must be a multiple of $100.")

            rem = int(amount_val)
            notes: Dict[int, int] = {}
            for d in (500, 200, 100):
                c = rem // d
                notes[d] = c
                rem %= d
        elif isinstance(amount_or_notes, dict):
            notes = amount_or_notes
        else:
            raise InvalidAmountException("Invalid deposit format.")

        try:
            total_deposited = self.vault_service.deposit_notes(notes)
            new_balance = account.apply_deposit(float(total_deposited))
            self.account_repo.save(account)

            tx_id = self.transaction_repo.record_transaction(
                TransactionRecord(
                    account_number=account_number,
                    transaction_type="DEPOSIT",
                    amount=float(total_deposited),
                    status="SUCCESS",
                    failure_reason=None,
                )
            )

            return {
                "transaction_id": tx_id,
                "account_number": account_number,
                "deposited_amount": total_deposited,
                "deposited_notes": notes,
                "new_balance": new_balance,
            }
        except AtmBaseException as e:
            self.transaction_repo.record_transaction(
                TransactionRecord(
                    account_number=account_number,
                    transaction_type="DEPOSIT",
                    amount=0.0,
                    status="FAILED",
                    failure_reason=e.failure_reason,
                )
            )
            raise e

    def get_statement(self, account_number: str, limit: int = 10) -> List[TransactionRecord]:
        return self.transaction_repo.get_recent_by_account(account_number, limit)

    def change_security_pin(
        self, account_number: str, old_pin: str, new_pin: str
    ) -> bool:
        if not (new_pin.isdigit() and len(new_pin) in (4, 6)):
            raise InvalidAmountException("New PIN must be exactly 4 or 6 numeric digits.")

        account = self.account_repo.get_by_number(account_number)
        if account is None:
            raise AccountNotFoundException(f"Account '{account_number}' not found.")

        if account.is_locked:
            raise AccountLockedException("Cannot change PIN for locked account.")

        if not self.hash_provider.verify_pin(old_pin, account.salt, account.pin_hash):
            raise InvalidAmountException("Current PIN verification failed.")

        new_salt = self.hash_provider.generate_salt()
        new_hash = self.hash_provider.hash_pin(new_pin, new_salt)

        account.salt = new_salt
        account.pin_hash = new_hash
        self.account_repo.save(account)
        return True
