"""
Security and Cryptography Facade for the Advanced ATM Simulator.
Provides backward-compatible functional interfaces delegating to Domain Services
(Pbkdf2PepperHashProvider and AuthenticationService).
"""

import sqlite3
from typing import Any, Dict, Optional

from core.domain.account import Account
from core.exceptions import (
    AccountAlreadyExistsException,
    AccountLockedException,
    AccountNotFoundException,
    AuthenticationFailedException,
    InvalidAmountException,
)
from core.repositories.account_repo import SqliteAccountRepository
from core.repositories.transaction_repo import SqliteTransactionRepository
from core.services.authentication import AuthenticationService
from core.services.security import Pbkdf2PepperHashProvider
from database.connection import immediate_transaction

_default_hash_provider = Pbkdf2PepperHashProvider()


def generate_salt() -> str:
    """Generates a cryptographically secure random hexadecimal salt."""
    return _default_hash_provider.generate_salt()


def hash_pin_v3(pin: str, salt: str, pepper: Optional[str] = None) -> str:
    """Computes Version 3 PBKDF2-HMAC-SHA256 hash using a server-side pepper."""
    return _default_hash_provider.hash_pin(pin, salt, pepper)


def hash_pin(pin: str, salt: str, pepper: Optional[str] = None) -> str:
    """Hashes a PIN string with salt and pepper."""
    return _default_hash_provider.hash_pin(pin, salt, pepper)


def verify_pin(
    pin: str, salt: str, expected_hash: str, pepper: Optional[str] = None
) -> bool:
    """Verifies if the provided PIN matches expected_hash under constant-time check."""
    return _default_hash_provider.verify_pin(pin, salt, expected_hash, pepper)


def authenticate_user(
    conn: sqlite3.Connection, account_number: str, pin: str
) -> Dict[str, Any]:
    """Authenticates user credentials and manages brute-force lockout."""
    exception_to_raise: Optional[Exception] = None
    account_dict: Optional[Dict[str, Any]] = None

    with immediate_transaction(conn):
        account_repo = SqliteAccountRepository(conn)
        tx_repo = SqliteTransactionRepository(conn)
        auth_service = AuthenticationService(account_repo, tx_repo, _default_hash_provider)
        try:
            account = auth_service.authenticate(account_number, pin)
            account_dict = {
                "account_number": account.account_number,
                "account_holder": account.account_holder,
                "pin_hash": account.pin_hash,
                "salt": account.salt,
                "balance": account.balance,
                "is_locked": 1 if account.is_locked else 0,
                "failed_attempts": account.failed_attempts,
                "created_at": account.created_at,
            }
        except (AuthenticationFailedException, AccountLockedException, AccountNotFoundException) as e:
            exception_to_raise = e

    if exception_to_raise is not None:
        raise exception_to_raise

    return account_dict or {}


def unlock_account(conn: sqlite3.Connection, account_number: str) -> bool:
    """Unlocks a customer account and resets failed attempt counters."""
    with immediate_transaction(conn):
        account_repo = SqliteAccountRepository(conn)
        tx_repo = SqliteTransactionRepository(conn)
        auth_service = AuthenticationService(account_repo, tx_repo, _default_hash_provider)
        return auth_service.unlock_account(account_number)


def create_account(
    conn: sqlite3.Connection,
    account_number: Optional[str] = None,
    account_holder: str = "",
    pin: str = "",
    initial_balance: float = 0.0,
) -> Dict[str, Any]:
    """Registers a new customer account in the database."""
    with immediate_transaction(conn):
        account_repo = SqliteAccountRepository(conn)
        tx_repo = SqliteTransactionRepository(conn)
        auth_service = AuthenticationService(account_repo, tx_repo, _default_hash_provider)

        # If custom account_number is provided explicitly
        if account_number and account_number.strip():
            acc_num = str(account_number).strip()
            holder = str(account_holder).strip()
            if not holder:
                raise InvalidAmountException("Account holder name cannot be empty.")
            if not (isinstance(pin, str) and pin.isdigit() and len(pin) in (4, 6)):
                raise InvalidAmountException("PIN must be exactly 4 or 6 numeric digits.")
            if initial_balance < 0:
                raise InvalidAmountException("Initial balance cannot be negative.")

            if account_repo.get_by_number(acc_num) is not None:
                raise AccountAlreadyExistsException(
                    f"Account number '{acc_num}' already exists in the system."
                )

            salt = _default_hash_provider.generate_salt()
            pin_hash = _default_hash_provider.hash_pin(pin, salt)
            acc = Account(
                account_number=acc_num,
                account_holder=holder,
                pin_hash=pin_hash,
                salt=salt,
                balance=float(initial_balance),
                is_locked=False,
                failed_attempts=0,
            )
            account_repo.create(acc)
            from core.domain.transaction import TransactionRecord

            tx_repo.record_transaction(
                TransactionRecord(
                    account_number=acc_num,
                    transaction_type="DEPOSIT",
                    amount=float(initial_balance),
                    status="SUCCESS",
                    failure_reason="ACCOUNT_CREATED",
                )
            )
            return {
                "account_number": acc.account_number,
                "account_holder": acc.account_holder,
                "balance": acc.balance,
                "is_locked": 0,
                "failed_attempts": 0,
            }
        else:
            acc = auth_service.create_customer_account(account_holder, pin, initial_balance)
            return {
                "account_number": acc.account_number,
                "account_holder": acc.account_holder,
                "balance": acc.balance,
                "is_locked": 0,
                "failed_attempts": 0,
            }
