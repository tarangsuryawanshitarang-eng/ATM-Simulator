"""
Security and Cryptography module for the Advanced ATM Simulator (Version 3).
Implements Version 3 Cryptographic Hash Architecture:
  - PBKDF2-HMAC-SHA256 (100,000 rounds)
  - Cryptographically secure 16-byte unique salts
  - Server-side Secret Pepper pre-processing via HMAC-SHA256
  - Constant-time comparison to prevent timing attacks
  - Account lockout threshold enforcement (>= 3 attempts)
  - Transparent auto-migration from legacy hashes to Version 3
"""

import hashlib
import hmac
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


def hash_pin_v3(pin: str, salt: str, pepper: Optional[str] = None) -> str:
    """
    Version 3 Hash Function:
    Combines PIN + Server-Side Secret Pepper (via HMAC-SHA256),
    followed by PBKDF2-HMAC-SHA256 (100,000 iterations) with a unique 16-byte salt.
    Returns version-tagged string: 'v3$<hex_digest>'.
    """
    if not isinstance(pin, str) or not pin:
        raise ValueError("PIN must be a non-empty string.")
    if not isinstance(salt, str) or not salt:
        raise ValueError("Salt must be a non-empty string.")

    pepper_key = (pepper or config.SECURITY_PEPPER_V3).encode("utf-8")
    
    # Step 1: Pre-process PIN with secret pepper via HMAC-SHA256
    peppered_digest = hmac.new(
        key=pepper_key,
        msg=pin.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()

    # Step 2: PBKDF2-HMAC-SHA256 key derivation with unique salt
    derived_key = hashlib.pbkdf2_hmac(
        hash_name=config.PBKDF2_HASH_NAME,
        password=peppered_digest,
        salt=salt.encode("utf-8"),
        iterations=config.PBKDF2_ITERATIONS,
    )
    return f"v3${derived_key.hex()}"


def hash_pin(pin: str, salt: str, pepper: Optional[str] = None) -> str:
    """Default hashing interface. Uses Version 3 cryptographic formulation."""
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
    logs authentication audit trails atomically, and auto-upgrades legacy hashes to v3.
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
                # Verify PIN (supports v3 and legacy)
                is_valid = verify_pin(pin, account["salt"], account["pin_hash"])

                if is_valid:
                    # Auto-upgrade legacy hashes to Version 3 upon successful login
                    if not account["pin_hash"].startswith("v3$"):
                        new_v3_hash = hash_pin_v3(pin, account["salt"])
                        conn.execute(
                            "UPDATE accounts SET pin_hash = ? WHERE account_number = ?;",
                            (new_v3_hash, account_number),
                        )
                        account["pin_hash"] = new_v3_hash

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
