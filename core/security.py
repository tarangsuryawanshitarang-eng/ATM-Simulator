"""
Security and Cryptography module for the Advanced ATM Simulator.
Implements PBKDF2-HMAC-SHA256 hashing, unique salts, constant-time comparison,
and account lockout threshold enforcement.
"""

import hashlib
import hmac
import os
import secrets
import sqlite3
from typing import Any, Dict, Optional

import config
from core.exceptions import (
    AccountAlreadyExistsException,
    AccountLockedException,
    AccountNotFoundException,
    AuthenticationFailedException,
    InvalidAmountException,
)
from database.connection import immediate_transaction

SECURITY_PEPPER = getattr(
    config,
    "SECURITY_PEPPER_V3",
    os.environ.get(
        "ATM_SECURITY_PEPPER",
        "s3cr3t_ATM_p3pp3r_k3y_v3_98a7b6c5d4e3f210a8b9c0d1e2f3a4b5",
    ),
)


def generate_salt() -> str:
    """Generates a cryptographically secure random hexadecimal salt."""
    return secrets.token_hex(config.SALT_BYTE_LENGTH)


def hash_pin_v3(pin: str, salt: str, pepper: Optional[str] = None) -> str:
    """Computes Version 3 PBKDF2-HMAC-SHA256 hash using a server-side pepper."""
    if not isinstance(pin, str) or not pin:
        raise ValueError("PIN must be a non-empty string.")
    if not isinstance(salt, str) or not salt:
        raise ValueError("Salt must be a non-empty string.")

    active_pepper = pepper or SECURITY_PEPPER
    peppered_digest = hmac.new(
        key=active_pepper.encode("utf-8"),
        msg=pin.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()

    derived_key = hashlib.pbkdf2_hmac(
        hash_name=config.PBKDF2_HASH_NAME,
        password=peppered_digest,
        salt=salt.encode("utf-8"),
        iterations=config.PBKDF2_ITERATIONS,
    )
    return f"v3${derived_key.hex()}"


def hash_pin(pin: str, salt: str, pepper: Optional[str] = None) -> str:
    """Hashes a PIN string with salt and pepper."""
    return hash_pin_v3(pin, salt, pepper)


def verify_pin(
    pin: str, salt: str, expected_hash: str, pepper: Optional[str] = None
) -> bool:
    """
    Verifies if the provided PIN matches expected_hash under the given salt and pepper.
    Supports both Version 3 (v3$) peppered hashes and legacy PBKDF2 hashes.
    Uses constant-time comparison to prevent timing attacks.
    """
    if not isinstance(expected_hash, str) or not expected_hash:
        return False

    if expected_hash.startswith("v3$"):
        actual_hash = hash_pin_v3(pin, salt, pepper)
        return secrets.compare_digest(actual_hash, expected_hash)
    else:
        # Legacy v1/v2 hash verification (unpeppered PBKDF2)
        derived_legacy = hashlib.pbkdf2_hmac(
            hash_name=config.PBKDF2_HASH_NAME,
            password=pin.encode("utf-8"),
            salt=salt.encode("utf-8"),
            iterations=config.PBKDF2_ITERATIONS,
        ).hex()
        return secrets.compare_digest(derived_legacy, expected_hash)


def authenticate_user(
    conn: sqlite3.Connection, account_number: str, pin: str
) -> Dict[str, Any]:
    """
    Authenticates a user against the database.
    Manages failed attempt counters, triggers immediate lockout at threshold,
    and logs authentication audit trails atomically.
    Ensures state updates (failed attempts / lockouts) commit prior to raising exceptions.
    """
    account = None
    exception_to_raise: Optional[Exception] = None

    with immediate_transaction(conn):
        cursor = conn.execute(
            """
            SELECT account_number, account_holder, pin_hash, salt, balance, is_locked, failed_attempts
            FROM accounts
            WHERE account_number = ?;
            """,
            (account_number,),
        )
        row = cursor.fetchone()

        if row is None:
            exception_to_raise = AccountNotFoundException(f"Account '{account_number}' not found.")
        else:
            account = dict(row)

            # Check if already locked
            if account["is_locked"] == 1 or account["failed_attempts"] >= config.MAX_FAILED_ATTEMPTS:
                if account["is_locked"] == 0:
                    conn.execute(
                        "UPDATE accounts SET is_locked = 1 WHERE account_number = ?;",
                        (account_number,),
                    )
                conn.execute(
                    """
                    INSERT INTO transactions (account_number, transaction_type, amount, status, failure_reason)
                    VALUES (?, 'AUTHENTICATE', 0.0, 'REJECTED', 'ACCOUNT_LOCKED');
                    """,
                    (account_number,),
                )
                exception_to_raise = AccountLockedException(
                    f"Account '{account_number}' is locked due to excessive failed attempts. Please contact support."
                )
            else:
                # Verify PIN
                is_valid = verify_pin(pin, account["salt"], account["pin_hash"])

                if is_valid:
                    # Reset failed attempts if previously incremented
                    if account["failed_attempts"] > 0:
                        conn.execute(
                            "UPDATE accounts SET failed_attempts = 0 WHERE account_number = ?;",
                            (account_number,),
                        )
                        account["failed_attempts"] = 0

                    # Log successful authentication
                    conn.execute(
                        """
                        INSERT INTO transactions (account_number, transaction_type, amount, status, failure_reason)
                        VALUES (?, 'AUTHENTICATE', 0.0, 'SUCCESS', NULL);
                        """,
                        (account_number,),
                    )
                else:
                    new_failed_attempts = account["failed_attempts"] + 1
                    remaining = max(0, config.MAX_FAILED_ATTEMPTS - new_failed_attempts)

                    if new_failed_attempts >= config.MAX_FAILED_ATTEMPTS:
                        conn.execute(
                            """
                            UPDATE accounts 
                            SET failed_attempts = ?, is_locked = 1 
                            WHERE account_number = ?;
                            """,
                            (new_failed_attempts, account_number),
                        )
                        conn.execute(
                            """
                            INSERT INTO transactions (account_number, transaction_type, amount, status, failure_reason)
                            VALUES (?, 'LOCKOUT', 0.0, 'REJECTED', 'EXCEEDED_MAX_FAILED_ATTEMPTS');
                            """,
                            (account_number,),
                        )
                        exception_to_raise = AccountLockedException(
                            f"Invalid PIN. Maximum attempts ({config.MAX_FAILED_ATTEMPTS}) exceeded. Account '{account_number}' is now LOCKED."
                        )
                    else:
                        conn.execute(
                            """
                            UPDATE accounts 
                            SET failed_attempts = ? 
                            WHERE account_number = ?;
                            """,
                            (new_failed_attempts, account_number),
                        )
                        conn.execute(
                            """
                            INSERT INTO transactions (account_number, transaction_type, amount, status, failure_reason)
                            VALUES (?, 'AUTHENTICATE', 0.0, 'FAILED', 'INVALID_PIN');
                            """,
                            (account_number,),
                        )
                        exception_to_raise = AuthenticationFailedException(
                            f"Invalid PIN entered. {remaining} attempt(s) remaining before account lockout.",
                            remaining_attempts=remaining,
                        )

    # Raise domain exception after immediate_transaction commits state updates
    if exception_to_raise is not None:
        raise exception_to_raise

    return account


def unlock_account(conn: sqlite3.Connection, account_number: str) -> bool:
    """
    Administrative function to unlock a locked customer account and reset failed attempts.
    Logs an audit event in the transactions table.
    """
    with immediate_transaction(conn):
        cursor = conn.execute(
            "SELECT account_number, account_holder, is_locked FROM accounts WHERE account_number = ?;",
            (account_number,),
        )
        row = cursor.fetchone()
        if row is None:
            raise AccountNotFoundException(f"Account '{account_number}' not found.")

        conn.execute(
            """
            UPDATE accounts 
            SET is_locked = 0, failed_attempts = 0 
            WHERE account_number = ?;
            """,
            (account_number,),
        )
        conn.execute(
            """
            INSERT INTO transactions (account_number, transaction_type, amount, status, failure_reason)
            VALUES (?, 'AUTHENTICATE', 0.0, 'SUCCESS', 'ADMIN_UNLOCKED');
            """,
            (account_number,),
        )
        return True


def create_account(
    conn: sqlite3.Connection,
    account_number: str,
    account_holder: str,
    pin: str,
    initial_balance: float = 0.0,
) -> Dict[str, Any]:
    """
    Registers a new customer account in the database.
    Validates account number, holder name, PIN length, and initial balance.
    Hashes the PIN with a unique random cryptographic salt and records an audit log.
    """
    account_number = str(account_number).strip()
    account_holder = str(account_holder).strip()

    if not account_number:
        raise InvalidAmountException("Account number cannot be empty.")
    if len(account_number) < 3 or len(account_number) > 20:
        raise InvalidAmountException("Account number must be between 3 and 20 characters.")
    if not account_holder:
        raise InvalidAmountException("Account holder name cannot be empty.")
    if not (isinstance(pin, str) and pin.isdigit() and len(pin) in (4, 6)):
        raise InvalidAmountException("PIN must be exactly 4 or 6 numeric digits.")
    if initial_balance < 0:
        raise InvalidAmountException("Initial balance cannot be negative.")

    with immediate_transaction(conn):
        cursor = conn.execute(
            "SELECT account_number FROM accounts WHERE account_number = ?;",
            (account_number,),
        )
        if cursor.fetchone() is not None:
            raise AccountAlreadyExistsException(
                f"Account number '{account_number}' already exists in the system."
            )

        salt = generate_salt()
        pin_hash = hash_pin(pin, salt)

        conn.execute(
            """
            INSERT INTO accounts (account_number, account_holder, pin_hash, salt, balance, is_locked, failed_attempts)
            VALUES (?, ?, ?, ?, ?, 0, 0);
            """,
            (account_number, account_holder, pin_hash, salt, float(initial_balance)),
        )

        # Record initial ledger transaction
        conn.execute(
            """
            INSERT INTO transactions (account_number, transaction_type, amount, status, failure_reason)
            VALUES (?, 'DEPOSIT', ?, 'SUCCESS', 'ACCOUNT_CREATED');
            """,
            (account_number, float(initial_balance)),
        )

    return {
        "account_number": account_number,
        "account_holder": account_holder,
        "balance": float(initial_balance),
        "is_locked": 0,
        "failed_attempts": 0,
    }


