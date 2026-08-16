"""
Transaction Engine Facade for the Advanced ATM Simulator.
Provides backward-compatible functional interfaces delegating to BankingTransactionService.
"""

import sqlite3
from typing import Any, Dict, List, Optional

from core.domain.transaction import TransactionRecord
from core.exceptions import AccountNotFoundException
from core.repositories.account_repo import SqliteAccountRepository
from core.repositories.transaction_repo import SqliteTransactionRepository
from core.repositories.vault_repo import SqliteVaultRepository
from core.services.security import Pbkdf2PepperHashProvider
from core.services.transaction import BankingTransactionService
from core.services.vault import VaultManagerService
from database.connection import immediate_transaction


def _get_transaction_service(conn: sqlite3.Connection) -> BankingTransactionService:
    account_repo = SqliteAccountRepository(conn)
    tx_repo = SqliteTransactionRepository(conn)
    vault_repo = SqliteVaultRepository(conn)
    vault_service = VaultManagerService(vault_repo)
    hash_provider = Pbkdf2PepperHashProvider()
    return BankingTransactionService(account_repo, tx_repo, vault_service, hash_provider)


def get_account_details(conn: sqlite3.Connection, account_number: str) -> Dict[str, Any]:
    """Retrieves account record dictionary from the database."""
    account_repo = SqliteAccountRepository(conn)
    account = account_repo.get_by_number(account_number)
    if account is None:
        raise AccountNotFoundException(f"Account '{account_number}' not found.")
    return {
        "account_number": account.account_number,
        "account_holder": account.account_holder,
        "balance": account.balance,
        "is_locked": 1 if account.is_locked else 0,
        "failed_attempts": account.failed_attempts,
        "created_at": account.created_at,
    }


def get_balance(conn: sqlite3.Connection, account_number: str) -> float:
    """Performs an inquiry of the current account balance and logs the inquiry."""
    with immediate_transaction(conn):
        service = _get_transaction_service(conn)
        return service.check_balance(account_number)


def withdraw(
    conn: sqlite3.Connection, account_number: str, amount: float
) -> Dict[str, Any]:
    """Executes an atomic withdrawal."""
    with immediate_transaction(conn):
        service = _get_transaction_service(conn)
        return service.withdraw_cash(account_number, amount)


def deposit(
    conn: sqlite3.Connection, account_number: str, notes_or_amount: Any
) -> Dict[str, Any]:
    """Executes an atomic deposit."""
    with immediate_transaction(conn):
        service = _get_transaction_service(conn)
        return service.deposit_cash(account_number, notes_or_amount)


def get_transaction_history(
    conn: sqlite3.Connection, account_number: str, limit: int = 10
) -> List[Dict[str, Any]]:
    """Retrieves recent transaction audit history for an account."""
    service = _get_transaction_service(conn)
    records = service.get_statement(account_number, limit)
    return [
        {
            "transaction_id": r.transaction_id,
            "account_number": r.account_number,
            "transaction_type": r.transaction_type,
            "amount": r.amount,
            "status": r.status,
            "failure_reason": r.failure_reason,
            "timestamp": r.timestamp,
        }
        for r in records
    ]


def change_pin(
    conn: sqlite3.Connection, account_number: str, old_pin: str, new_pin: str
) -> bool:
    """Validates current PIN and updates the account with new salted hash."""
    with immediate_transaction(conn):
        service = _get_transaction_service(conn)
        return service.change_security_pin(account_number, old_pin, new_pin)
