"""
Authentication and User Account Domain Service.
Orchestrates login verification, account creation, brute-force lockout, and unlocking.
"""

from typing import Optional

import config
from core.domain.account import Account
from core.domain.transaction import TransactionRecord
from core.exceptions import (
    AccountAlreadyExistsException,
    AccountLockedException,
    AccountNotFoundException,
    AuthenticationFailedException,
    InvalidAmountException,
)
from core.interfaces.repositories import IAccountRepository, ITransactionRepository
from core.interfaces.security import IAuthenticationService, IHashProvider
from core.services.security import Pbkdf2PepperHashProvider


class AuthenticationService(IAuthenticationService):
    """
    Concrete service managing user authentication, security policies,
    and administrative customer registration.
    """

    def __init__(
        self,
        account_repo: IAccountRepository,
        transaction_repo: ITransactionRepository,
        hash_provider: Optional[IHashProvider] = None,
    ):
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo
        self.hash_provider = hash_provider or Pbkdf2PepperHashProvider()

    def authenticate(self, account_number: str, pin: str) -> Account:
        """
        Authenticates an account by account number and PIN.
        Enforces maximum failed attempt lockout threshold and logs authentication events.
        """
        account = self.account_repo.get_by_number(account_number)
        if account is None:
            raise AccountNotFoundException(f"Account '{account_number}' not found.")

        # Check if already locked
        if account.is_locked or account.failed_attempts >= config.MAX_FAILED_ATTEMPTS:
            if not account.is_locked:
                account.is_locked = True
                self.account_repo.save(account)

            self.transaction_repo.record_transaction(
                TransactionRecord(
                    account_number=account.account_number,
                    transaction_type="AUTHENTICATE",
                    amount=0.0,
                    status="REJECTED",
                    failure_reason="ACCOUNT_LOCKED",
                )
            )
            raise AccountLockedException(
                f"Account '{account.account_number}' is locked due to excessive failed attempts. Please contact support."
            )

        # Verify PIN
        is_valid = self.hash_provider.verify_pin(pin, account.salt, account.pin_hash)

        if is_valid:
            # Auto-upgrade legacy hashes to Version 3 if needed
            if not account.pin_hash.startswith("v3$"):
                new_v3_hash = self.hash_provider.hash_pin(pin, account.salt)
                account.pin_hash = new_v3_hash
                self.account_repo.save(account)

            if account.failed_attempts > 0:
                account.reset_failed_attempts()
                self.account_repo.save(account)

            self.transaction_repo.record_transaction(
                TransactionRecord(
                    account_number=account.account_number,
                    transaction_type="AUTHENTICATE",
                    amount=0.0,
                    status="SUCCESS",
                    failure_reason=None,
                )
            )
            return account
        else:
            is_newly_locked = account.record_failed_attempt(config.MAX_FAILED_ATTEMPTS)
            self.account_repo.save(account)

            remaining = max(0, config.MAX_FAILED_ATTEMPTS - account.failed_attempts)

            if is_newly_locked:
                self.transaction_repo.record_transaction(
                    TransactionRecord(
                        account_number=account.account_number,
                        transaction_type="LOCKOUT",
                        amount=0.0,
                        status="REJECTED",
                        failure_reason="EXCEEDED_MAX_FAILED_ATTEMPTS",
                    )
                )
                raise AccountLockedException(
                    f"Invalid PIN. Maximum attempts ({config.MAX_FAILED_ATTEMPTS}) exceeded. Account '{account.account_number}' is now LOCKED."
                )
            else:
                self.transaction_repo.record_transaction(
                    TransactionRecord(
                        account_number=account.account_number,
                        transaction_type="AUTHENTICATE",
                        amount=0.0,
                        status="FAILED",
                        failure_reason="INVALID_PIN",
                    )
                )
                raise AuthenticationFailedException(
                    f"Invalid PIN entered. {remaining} attempt(s) remaining before account lockout.",
                    remaining_attempts=remaining,
                )

    def unlock_account(self, account_number: str) -> bool:
        """
        Unlocks a customer account and resets failed attempt counters.
        """
        account = self.account_repo.get_by_number(account_number)
        if account is None:
            raise AccountNotFoundException(f"Account '{account_number}' not found.")

        account.unlock()
        self.account_repo.save(account)

        self.transaction_repo.record_transaction(
            TransactionRecord(
                account_number=account.account_number,
                transaction_type="AUTHENTICATE",
                amount=0.0,
                status="SUCCESS",
                failure_reason="ADMIN_UNLOCKED",
            )
        )
        return True

    def create_customer_account(
        self, account_holder: str, pin: str, initial_balance: float = 0.0
    ) -> Account:
        """
        Registers a new customer account using auto-generated account numbering.
        """
        holder = str(account_holder).strip()
        if not holder:
            raise InvalidAmountException("Customer name cannot be blank.")
        if not (isinstance(pin, str) and pin.isdigit() and len(pin) in (4, 6)):
            raise InvalidAmountException("PIN must be exactly 4 or 6 numeric digits.")
        if initial_balance < 0:
            raise InvalidAmountException("Initial balance cannot be negative.")

        account_number = self.account_repo.get_next_account_number()
        salt = self.hash_provider.generate_salt()
        pin_hash = self.hash_provider.hash_pin(pin, salt)

        new_account = Account(
            account_number=account_number,
            account_holder=holder,
            pin_hash=pin_hash,
            salt=salt,
            balance=initial_balance,
            is_locked=False,
            failed_attempts=0,
        )
        self.account_repo.create(new_account)

        self.transaction_repo.record_transaction(
            TransactionRecord(
                account_number=account_number,
                transaction_type="DEPOSIT",
                amount=initial_balance,
                status="SUCCESS",
                failure_reason="ACCOUNT_CREATED",
            )
        )
        return new_account

    def delete_customer_account(self, account_number: str) -> bool:
        """
        Closes and permanently deletes a customer account and cleans up associated records.
        """
        account = self.account_repo.get_by_number(account_number)
        if account is None:
            raise AccountNotFoundException(f"Account '{account_number}' not found.")

        return self.account_repo.delete(account_number)

