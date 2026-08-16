"""
Unit Tests for Security & Cryptography Subsystem (Version 3).
Tests PBKDF2 hashing, unique random salts, server-side Pepper integration,
constant-time verification, brute-force lockout, and legacy hash auto-migration.
"""

import hashlib
import sqlite3
import unittest
from pathlib import Path

import config
from core.exceptions import (
    AccountLockedException,
    AccountNotFoundException,
    AuthenticationFailedException,
)
from core.security import (
    authenticate_user,
    generate_salt,
    hash_pin,
    hash_pin_v3,
    unlock_account,
    verify_pin,
)
from database.connection import get_db_connection
from database.seeder import seed_data


class TestSecuritySubsystem(unittest.TestCase):
    """Test suite verifying cryptographic functions and lockout policies."""

    def setUp(self) -> None:
        """Create an isolated test database."""
        self.test_db_path = Path("test_security_atm.db")
        seed_data(db_path=self.test_db_path, reset=True)
        self.conn = get_db_connection(self.test_db_path)

    def tearDown(self) -> None:
        """Clean up database connections and test files."""
        self.conn.close()
        if self.test_db_path.exists():
            try:
                self.test_db_path.unlink()
            except PermissionError:
                pass

    def test_salt_uniqueness_and_length(self) -> None:
        """Verifies that generated salts are unique and meet the 16-byte hex requirement."""
        salt1 = generate_salt()
        salt2 = generate_salt()
        self.assertNotEqual(salt1, salt2)
        self.assertEqual(len(salt1), config.SALT_BYTE_LENGTH * 2)  # 16 bytes = 32 hex chars

    def test_pin_hashing_v3_format_and_verification(self) -> None:
        """Verifies Version 3 PBKDF2 + Pepper hash computation and verification."""
        pin = "1234"
        salt = generate_salt()
        v3_hash = hash_pin_v3(pin, salt)

        # Must start with v3$ identifier
        self.assertTrue(v3_hash.startswith("v3$"))
        self.assertTrue(verify_pin(pin, salt, v3_hash))
        self.assertFalse(verify_pin("9999", salt, v3_hash))
        self.assertFalse(verify_pin("12345", salt, v3_hash))

    def test_pepper_defense_and_sensitivity(self) -> None:
        """
        Verifies that without the correct server-side Pepper, PIN verification fails
        even if the salt and PIN are known.
        """
        pin = "1234"
        salt = generate_salt()
        correct_pepper = "correct_server_secret_pepper_12345"
        wrong_pepper = "wrong_server_secret_pepper_99999"

        v3_hash = hash_pin_v3(pin, salt, pepper=correct_pepper)

        # Verification with correct pepper must succeed
        self.assertTrue(verify_pin(pin, salt, v3_hash, pepper=correct_pepper))

        # Verification with wrong pepper must fail
        self.assertFalse(verify_pin(pin, salt, v3_hash, pepper=wrong_pepper))

    def test_backward_compatibility_and_auto_upgrade(self) -> None:
        """
        Verifies that legacy unpeppered hashes are verified and automatically
        upgraded to Version 3 (v3$) hashes upon successful user login.
        """
        account_num = "10001"
        salt = generate_salt()
        # Create a legacy hash manually without v3 pepper
        legacy_hash = hashlib.pbkdf2_hmac(
            config.PBKDF2_HASH_NAME,
            "1234".encode("utf-8"),
            salt.encode("utf-8"),
            config.PBKDF2_ITERATIONS,
        ).hex()

        self.conn.execute(
            "UPDATE accounts SET pin_hash = ?, salt = ? WHERE account_number = ?;",
            (legacy_hash, salt, account_num),
        )

        # Authenticate user with legacy hash
        account = authenticate_user(self.conn, account_num, "1234")
        self.assertEqual(account["account_number"], account_num)

        # Verify that the database record has been auto-upgraded to v3$
        row = self.conn.execute("SELECT pin_hash FROM accounts WHERE account_number = ?;", (account_num,)).fetchone()
        self.assertTrue(row["pin_hash"].startswith("v3$"))

    def test_authentication_success(self) -> None:
        """Verifies successful authentication for demo account 10001."""
        account = authenticate_user(self.conn, "10001", "1234")
        self.assertEqual(account["account_number"], "10001")
        self.assertEqual(account["account_holder"], "Alice Smith")
        self.assertEqual(account["failed_attempts"], 0)

        # Verify audit log recorded SUCCESS
        cursor = self.conn.execute(
            "SELECT transaction_type, status FROM transactions WHERE account_number = '10001' ORDER BY transaction_id DESC LIMIT 1;"
        )
        tx = cursor.fetchone()
        self.assertIsNotNone(tx)
        self.assertEqual(tx["transaction_type"], "AUTHENTICATE")
        self.assertEqual(tx["status"], "SUCCESS")

    def test_authentication_invalid_pin_and_lockout_threshold(self) -> None:
        """
        Verifies that failed attempts increment sequentially and lock the account on the 3rd attempt.
        """
        account_num = "10002"  # Bob Jones, PIN 4321

        # Attempt 1: Failed
        with self.assertRaises(AuthenticationFailedException) as ctx1:
            authenticate_user(self.conn, account_num, "0000")
        self.assertEqual(ctx1.exception.remaining_attempts, 2)

        # Verify failed_attempts counter is 1
        row = self.conn.execute("SELECT failed_attempts, is_locked FROM accounts WHERE account_number = ?;", (account_num,)).fetchone()
        self.assertEqual(row["failed_attempts"], 1)
        self.assertEqual(row["is_locked"], 0)

        # Attempt 2: Failed
        with self.assertRaises(AuthenticationFailedException) as ctx2:
            authenticate_user(self.conn, account_num, "1111")
        self.assertEqual(ctx2.exception.remaining_attempts, 1)

        row = self.conn.execute("SELECT failed_attempts, is_locked FROM accounts WHERE account_number = ?;", (account_num,)).fetchone()
        self.assertEqual(row["failed_attempts"], 2)
        self.assertEqual(row["is_locked"], 0)

        # Attempt 3: Failed -> LOCKOUT Triggered
        with self.assertRaises(AccountLockedException):
            authenticate_user(self.conn, account_num, "2222")

        row = self.conn.execute("SELECT failed_attempts, is_locked FROM accounts WHERE account_number = ?;", (account_num,)).fetchone()
        self.assertEqual(row["failed_attempts"], 3)
        self.assertEqual(row["is_locked"], 1)

        # Verify LOCKOUT audit log
        cursor = self.conn.execute(
            "SELECT transaction_type, status, failure_reason FROM transactions WHERE account_number = ? ORDER BY transaction_id DESC LIMIT 1;",
            (account_num,)
        )
        tx = cursor.fetchone()
        self.assertEqual(tx["transaction_type"], "LOCKOUT")
        self.assertEqual(tx["status"], "REJECTED")

        # Subsequent attempt with correct PIN must still raise AccountLockedException
        with self.assertRaises(AccountLockedException):
            authenticate_user(self.conn, account_num, "4321")

    def test_failed_attempts_reset_on_successful_login(self) -> None:
        """Verifies failed_attempts resets to 0 if a valid PIN is supplied before reaching threshold."""
        account_num = "10003"  # Charlie Brown, PIN 9999

        # Attempt 1: Wrong PIN
        with self.assertRaises(AuthenticationFailedException):
            authenticate_user(self.conn, account_num, "0000")
        row = self.conn.execute("SELECT failed_attempts FROM accounts WHERE account_number = ?;", (account_num,)).fetchone()
        self.assertEqual(row["failed_attempts"], 1)

        # Attempt 2: Correct PIN -> Resets counter
        account = authenticate_user(self.conn, account_num, "9999")
        self.assertEqual(account["failed_attempts"], 0)
        row = self.conn.execute("SELECT failed_attempts FROM accounts WHERE account_number = ?;", (account_num,)).fetchone()
        self.assertEqual(row["failed_attempts"], 0)

    def test_non_existent_account(self) -> None:
        """Verifies AccountNotFoundException when account does not exist."""
        with self.assertRaises(AccountNotFoundException):
            authenticate_user(self.conn, "99999", "1234")

    def test_admin_unlock_account(self) -> None:
        """Verifies that an administrator can unlock a locked account."""
        account_num = "10004"  # Seeded as locked
        with self.assertRaises(AccountLockedException):
            authenticate_user(self.conn, account_num, "0000")

        # Admin unlocks account
        success = unlock_account(self.conn, account_num)
        self.assertTrue(success)

        # Verify account is now unlocked and can authenticate
        account = authenticate_user(self.conn, account_num, "0000")
        self.assertEqual(account["is_locked"], 0)
        self.assertEqual(account["failed_attempts"], 0)


if __name__ == "__main__":
    unittest.main()
