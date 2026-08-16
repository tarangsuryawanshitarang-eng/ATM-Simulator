"""
Unit Tests for Security & Cryptography Subsystem.
Tests PBKDF2 hashing, salt generation, constant-time verification, and brute-force lockout mechanisms.
"""

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
    verify_pin,
)
from database.connection import get_db_connection
from database.seeder import seed_data


class TestSecuritySubsystem(unittest.TestCase):
    """Test suite verifying cryptographic functions and lockout policies."""

    def setUp(self) -> None:
        """Create an isolated test database in memory or temporary file."""
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

    def test_pin_hashing_and_verification(self) -> None:
        """Verifies PBKDF2 hash computation and deterministic verification."""
        pin = "1234"
        salt = generate_salt()
        p_hash = hash_pin(pin, salt)

        self.assertTrue(verify_pin(pin, salt, p_hash))
        self.assertFalse(verify_pin("9999", salt, p_hash))
        self.assertFalse(verify_pin("12345", salt, p_hash))

    def test_authentication_success(self) -> None:
        """Verifies successful authentication for demo account 10001."""
        account = authenticate_user(self.conn, "10001", "1234")
        self.assertEqual(account["account_number"], "10001")
        self.assertEqual(account["account_holder"], "Aarav Sharma")
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
        from core.security import unlock_account

        account_num = "10004"  # Seeded as locked
        # Verify initially locked
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
