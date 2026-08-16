"""
Security and Cryptography module for the Advanced ATM Simulator.
Implements PBKDF2-HMAC-SHA256 hashing, unique salts, constant-time comparison,
and account lockout threshold enforcement.
"""

import hashlib
import secrets
import sqlite3
from typing import Any, Dict, Optional

import config
from core.exceptions import (
    AccountLockedException,
    AccountNotFoundException,
    AuthenticationFailedException,
)
from database.connection import immediate_transaction


def generate_salt() -> str:
    """Generates a cryptographically secure random hexadecimal salt."""
    return secrets.token_hex(config.SALT_BYTE_LENGTH)


def hash_pin(pin: str, salt: str) -> str:
    """
    Hashes a PIN string with the provided salt using PBKDF2-HMAC-SHA256.
    Returns the hexadecimal digest.
    """
    if not isinstance(pin, str) or not pin:
        raise ValueError("PIN must be a non-empty string.")
    if not isinstance(salt, str) or not salt:
        raise ValueError("Salt must be a non-empty string.")

    derived_key = hashlib.pbkdf2_hmac(
        hash_name=config.PBKDF2_HASH_NAME,
        password=pin.encode("utf-8"),
        salt=salt.encode("utf-8"),
        iterations=config.PBKDF2_ITERATIONS,
    )
    return derived_key.hex()


def verify_pin(pin: str, salt: str, expected_hash: str) -> bool:
    """
    Verifies if the provided PIN matches expected_hash under the given salt.
    Uses constant-time comparison to prevent timing attacks.
    """
    actual_hash = hash_pin(pin, salt)
    return secrets.compare_digest(actual_hash, expected_hash)


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
