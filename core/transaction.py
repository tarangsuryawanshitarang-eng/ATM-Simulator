"""
Transaction Engine for the Advanced ATM Simulator.
Enforces ACID compliance via explicit BEGIN IMMEDIATE TRANSACTION locking,
atomic balance updates, physical cassette synchronizations, and audit trail logging.
"""

import sqlite3
from typing import Any, Dict, List, Optional

from core.exceptions import (
    AccountLockedException,
    AccountNotFoundException,
    AtmBaseException,
    DatabaseTransactionError,
    InsufficientFundsException,
    InvalidAmountException,
)
from core.security import generate_salt, hash_pin, verify_pin
from core.vault import deposit_notes, dispense_cash
from database.connection import immediate_transaction


def _log_transaction(
    conn: sqlite3.Connection,
    account_number: str,
    tx_type: str,
    amount: float,
    status: str,
    failure_reason: Optional[str] = None,
) -> int:
    """Inserts an immutable audit record into the transactions table."""
    cursor = conn.execute(
        """
        INSERT INTO transactions (account_number, transaction_type, amount, status, failure_reason)
        VALUES (?, ?, ?, ?, ?);
        """,
        (account_number, tx_type, amount, status, failure_reason),
    )
    return cursor.lastrowid or 0


def get_account_details(conn: sqlite3.Connection, account_number: str) -> Dict[str, Any]:
    """Retrieves account record from the database."""
    cursor = conn.execute(
        """
        SELECT account_number, account_holder, balance, is_locked, failed_attempts, created_at
        FROM accounts
        WHERE account_number = ?;
        """,
        (account_number,),
    )
    row = cursor.fetchone()
    if row is None:
        raise AccountNotFoundException(f"Account '{account_number}' not found.")
    return dict(row)


def get_balance(conn: sqlite3.Connection, account_number: str) -> float:
    """
    Performs an inquiry of the current account balance and logs the inquiry.
    """
    exception_to_raise: Optional[Exception] = None
    balance_val = 0.0

    with immediate_transaction(conn):
        account = get_account_details(conn, account_number)
        if account["is_locked"] == 1:
            _log_transaction(
                conn, account_number, "BALANCE_INQUIRY", 0.0, "REJECTED", "ACCOUNT_LOCKED"
            )
            exception_to_raise = AccountLockedException(f"Account '{account_number}' is locked.")
        else:
            balance_val = float(account["balance"])
            _log_transaction(conn, account_number, "BALANCE_INQUIRY", balance_val, "SUCCESS", None)

    if exception_to_raise is not None:
        raise exception_to_raise

    return balance_val


def withdraw(
    conn: sqlite3.Connection, account_number: str, amount: float
) -> Dict[str, Any]:
    """
    Executes an atomic withdrawal.
    Verifies balance, allocates physical cassette notes, updates account balance,
    and logs the transaction.
    """
    if amount <= 0:
        raise InvalidAmountException("Withdrawal amount must be greater than zero.")

    exception_to_raise: Optional[Exception] = None
    result: Optional[Dict[str, Any]] = None

    with immediate_transaction(conn):
        account = get_account_details(conn, account_number)

        if account["is_locked"] == 1:
            _log_transaction(
                conn, account_number, "WITHDRAWAL", amount, "REJECTED", "ACCOUNT_LOCKED"
            )
            exception_to_raise = AccountLockedException(f"Account '{account_number}' is locked.")
        else:
            current_balance = float(account["balance"])
            if current_balance < amount:
                _log_transaction(
                    conn, account_number, "WITHDRAWAL", amount, "FAILED", "INSUFFICIENT_FUNDS"
                )
                exception_to_raise = InsufficientFundsException(
                    f"Insufficient funds. Current balance: ${current_balance:.2f}, Requested: ${amount:.2f}."
                )
            else:
                try:
                    # Dispense notes from physical vault cassettes
                    dispensed_notes = dispense_cash(conn, int(amount))

                    # Deduct balance from account
                    new_balance = round(current_balance - amount, 2)
                    conn.execute(
                        "UPDATE accounts SET balance = ? WHERE account_number = ?;",
                        (new_balance, account_number),
                    )

                    # Record success transaction
                    tx_id = _log_transaction(conn, account_number, "WITHDRAWAL", amount, "SUCCESS", None)

                    result = {
                        "transaction_id": tx_id,
                        "account_number": account_number,
                        "amount": amount,
                        "dispensed_notes": dispensed_notes,
                        "new_balance": new_balance,
                    }
                except AtmBaseException as e:
                    _log_transaction(conn, account_number, "WITHDRAWAL", amount, "FAILED", e.failure_reason)
                    exception_to_raise = e
                except Exception as e:
                    _log_transaction(conn, account_number, "WITHDRAWAL", amount, "FAILED", "DATABASE_ERROR")
                    exception_to_raise = DatabaseTransactionError(f"Withdrawal failed: {str(e)}")

    if exception_to_raise is not None:
        raise exception_to_raise

    return result or {}


def deposit(
    conn: sqlite3.Connection, account_number: str, notes: Dict[int, int]
) -> Dict[str, Any]:
    """
    Executes an atomic deposit with physical note breakdown.
    Increments vault cassette counts, credits account balance, and logs the transaction.
    """
    exception_to_raise: Optional[Exception] = None
    result: Optional[Dict[str, Any]] = None

    with immediate_transaction(conn):
        account = get_account_details(conn, account_number)

        if account["is_locked"] == 1:
            _log_transaction(
                conn, account_number, "DEPOSIT", 0.0, "REJECTED", "ACCOUNT_LOCKED"
            )
            exception_to_raise = AccountLockedException(f"Account '{account_number}' is locked.")
        else:
            try:
                total_deposited = deposit_notes(conn, notes)
                current_balance = float(account["balance"])
                new_balance = round(current_balance + total_deposited, 2)

                conn.execute(
                    "UPDATE accounts SET balance = ? WHERE account_number = ?;",
                    (new_balance, account_number),
                )

                tx_id = _log_transaction(
                    conn, account_number, "DEPOSIT", float(total_deposited), "SUCCESS", None
                )

                result = {
                    "transaction_id": tx_id,
                    "account_number": account_number,
                    "deposited_amount": total_deposited,
                    "deposited_notes": notes,
                    "new_balance": new_balance,
                }
            except AtmBaseException as e:
                _log_transaction(conn, account_number, "DEPOSIT", 0.0, "FAILED", e.failure_reason)
                exception_to_raise = e
            except Exception as e:
                _log_transaction(conn, account_number, "DEPOSIT", 0.0, "FAILED", "DATABASE_ERROR")
                exception_to_raise = DatabaseTransactionError(f"Deposit failed: {str(e)}")

    if exception_to_raise is not None:
        raise exception_to_raise

    return result or {}


def get_transaction_history(
    conn: sqlite3.Connection, account_number: str, limit: int = 10
) -> List[Dict[str, Any]]:
    """Retrieves recent transaction audit history for an account."""
    cursor = conn.execute(
        """
        SELECT transaction_id, account_number, transaction_type, amount, status, failure_reason, timestamp
        FROM transactions
        WHERE account_number = ?
        ORDER BY timestamp DESC, transaction_id DESC
        LIMIT ?;
        """,
        (account_number, limit),
    )
    return [dict(row) for row in cursor.fetchall()]


def change_pin(
    conn: sqlite3.Connection, account_number: str, old_pin: str, new_pin: str
) -> bool:
    """
    Validates current PIN and updates the account with a freshly salted hash for the new PIN.
    """
    if not (new_pin.isdigit() and len(new_pin) in (4, 6)):
        raise InvalidAmountException("New PIN must be exactly 4 or 6 numeric digits.")

    with immediate_transaction(conn):
        cursor = conn.execute(
            "SELECT pin_hash, salt, is_locked FROM accounts WHERE account_number = ?;",
            (account_number,),
        )
        row = cursor.fetchone()
        if row is None:
            raise AccountNotFoundException(f"Account '{account_number}' not found.")

        if row["is_locked"] == 1:
            raise AccountLockedException("Cannot change PIN for locked account.")

        if not verify_pin(old_pin, row["salt"], row["pin_hash"]):
            raise InvalidAmountException("Current PIN verification failed.")

        new_salt = generate_salt()
        new_hash = hash_pin(new_pin, new_salt)

        conn.execute(
            "UPDATE accounts SET pin_hash = ?, salt = ? WHERE account_number = ?;",
            (new_hash, new_salt, account_number),
        )
        return True
