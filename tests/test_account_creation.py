"""
Unit Tests for Customer Account Creation and Persistence.
Verifies account registration, uniqueness enforcement, initial balance logging,
persistence across seeder executions, and authentication of newly created accounts.
"""

import os
import sqlite3
import unittest
from pathlib import Path

import config
from core.exceptions import (
    AccountAlreadyExistsException,
    AccountLockedException,
    AuthenticationFailedException,
    InvalidAmountException,
)
from core.security import authenticate_user, create_account, unlock_account
from core.transaction import deposit, get_balance, withdraw
from database.connection import get_db_connection
from database.seeder import seed_data


class TestAccountCreationAndPersistence(unittest.TestCase):
    """Test suite verifying account creation, duplicate prevention, and data persistence."""

    def setUp(self) -> None:
        """Create an isolated test database."""
        self.test_db_path = Path("test_account_creation_atm.db")
        seed_data(db_path=self.test_db_path, reset=True)
        self.conn = get_db_connection(self.test_db_path)

    def tearDown(self) -> None:
        """Close connection and remove temporary test database."""
        self.conn.close()
        if self.test_db_path.exists():
            try:
                os.remove(self.test_db_path)
            except PermissionError:
                pass

    def test_create_account_success_with_zero_balance(self) -> None:
        """Verifies creating an account with $0.00 opening balance."""
        acc = create_account(self.conn, "20001", "David Miller", "5678", 0.0)
        self.assertEqual(acc["account_number"], "20001")
        self.assertEqual(acc["account_holder"], "David Miller")
        self.assertEqual(acc["balance"], 0.0)
        self.assertEqual(acc["is_locked"], 0)

        # Authenticate immediately
        auth = authenticate_user(self.conn, "20001", "5678")
        self.assertEqual(auth["account_number"], "20001")
        self.assertEqual(auth["balance"], 0.0)

    def test_create_account_success_with_initial_balance(self) -> None:
        """Verifies creating an account with initial deposit balance."""
        acc = create_account(self.conn, "20002", "Emma Watson", "1122", 1500.0)
        self.assertEqual(acc["balance"], 1500.0)

        # Verify balance inquiry
        bal = get_balance(self.conn, "20002")
        self.assertEqual(bal, 1500.0)

        # Perform withdrawal
        res = withdraw(self.conn, "20002", 500.0)
        self.assertEqual(res["new_balance"], 1000.0)

    def test_create_account_duplicate_account_number_fails(self) -> None:
        """Verifies that duplicate account numbers are strictly rejected."""
        create_account(self.conn, "20003", "Frank Castle", "9999", 100.0)

        with self.assertRaises(AccountAlreadyExistsException):
            create_account(self.conn, "20003", "Another Frank", "1234", 50.0)

    def test_create_account_invalid_pin_format(self) -> None:
        """Verifies PIN format validation (must be 4 or 6 digits)."""
        with self.assertRaises(InvalidAmountException):
            create_account(self.conn, "20004", "Grace Hopper", "123", 0.0)  # 3 digits

        with self.assertRaises(InvalidAmountException):
            create_account(self.conn, "20005", "Grace Hopper", "12345", 0.0)  # 5 digits

        with self.assertRaises(InvalidAmountException):
            create_account(self.conn, "20006", "Grace Hopper", "abcd", 0.0)  # non-digit

    def test_account_modifications_and_persistence_across_seeder(self) -> None:
        """
        Verifies that when an account's balance is changed (e.g. 10001) or unlocked (10004),
        subsequent calls to seed_data(reset=False) DO NOT overwrite or reset the live data.
        """
        # 1. Deposit into 10001 (seeded with 2500)
        deposit(self.conn, "10001", 1000.0)
        bal = get_balance(self.conn, "10001")
        self.assertEqual(bal, 3500.0)

        # 2. Unlock account 10004 (seeded as locked)
        unlock_account(self.conn, "10004")
        auth_10004 = authenticate_user(self.conn, "10004", "0000")
        self.assertEqual(auth_10004["is_locked"], 0)

        # 3. Create new user account 20010
        create_account(self.conn, "20010", "Persistent User", "4444", 750.0)

        # 4. Simulate application restart calling seed_data(reset=False)
        seed_data(db_path=self.test_db_path, reset=False)

        # 5. Verify that modified balance of 10001 was preserved
        conn2 = get_db_connection(self.test_db_path)
        try:
            bal_after = get_balance(conn2, "10001")
            self.assertEqual(bal_after, 3500.0, "Balance of 10001 should remain 3500.0 and NOT reset to 2500.0")

            # Verify that account 10004 remains unlocked
            auth_after = authenticate_user(conn2, "10004", "0000")
            self.assertEqual(auth_after["is_locked"], 0, "Account 10004 should remain UNLOCKED")

            # Verify that newly created account 20010 still exists and is accessible
            bal_new = get_balance(conn2, "20010")
            self.assertEqual(bal_new, 750.0, "New account 20010 must persist")
        finally:
            conn2.close()


if __name__ == "__main__":
    unittest.main()
