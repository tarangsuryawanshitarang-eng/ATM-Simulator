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
    AccountNotFoundException,
    AuthenticationFailedException,
    InvalidAmountException,
)
from core.security import authenticate_user, create_account, delete_account, unlock_account
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
        """Clean up test database."""
        self.conn.close()
        if self.test_db_path.exists():
            try:
                os.remove(self.test_db_path)
            except PermissionError:
                pass

    def test_create_account_with_zero_balance(self) -> None:
        """Verifies opening a customer account with $0.00 initial balance."""
        new_acc = create_account(
            self.conn,
            account_number="20001",
            account_holder="David Miller",
            pin="5555",
            initial_balance=0.0,
        )

        self.assertEqual(new_acc["account_number"], "20001")
        self.assertEqual(new_acc["account_holder"], "David Miller")
        self.assertEqual(new_acc["balance"], 0.0)

        auth_acc = authenticate_user(self.conn, "20001", "5555")
        self.assertEqual(auth_acc["account_holder"], "David Miller")
        self.assertEqual(auth_acc["balance"], 0.0)

    def test_create_account_with_initial_deposit(self) -> None:
        """Verifies opening a customer account with an initial opening balance."""
        new_acc = create_account(
            self.conn,
            account_number="20002",
            account_holder="Emma Watson",
            pin="6666",
            initial_balance=1500.0,
        )

        self.assertEqual(new_acc["balance"], 1500.0)

        bal = get_balance(self.conn, "20002")
        self.assertEqual(bal, 1500.0)

        tx_row = self.conn.execute(
            "SELECT transaction_type, amount, status, failure_reason FROM transactions WHERE account_number = '20002' AND transaction_type = 'DEPOSIT' ORDER BY transaction_id DESC LIMIT 1;"
        ).fetchone()
        self.assertIsNotNone(tx_row)
        self.assertEqual(tx_row["transaction_type"], "DEPOSIT")
        self.assertEqual(tx_row["amount"], 1500.0)
        self.assertEqual(tx_row["status"], "SUCCESS")

    def test_create_account_duplicate_account_number_rejected(self) -> None:
        """Verifies that creating an account with an existing account number raises AccountAlreadyExistsException."""
        with self.assertRaises(AccountAlreadyExistsException):
            create_account(
                self.conn,
                account_number="10001",
                account_holder="Duplicate User",
                pin="1111",
                initial_balance=100.0,
            )

    def test_create_account_validation(self) -> None:
        """Verifies PIN format and negative balance validation."""
        with self.assertRaises(InvalidAmountException):
            create_account(self.conn, "20003", "", "1234", 0.0)

        with self.assertRaises(InvalidAmountException):
            create_account(self.conn, "20004", "Grace Hopper", "1234", -50.0)

        with self.assertRaises(InvalidAmountException):
            create_account(self.conn, "20005", "Grace Hopper", "12345", 0.0)

        with self.assertRaises(InvalidAmountException):
            create_account(self.conn, "20006", "Grace Hopper", "abcd", 0.0)

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

    def test_delete_customer_account(self) -> None:
        """Verifies administrator ability to permanently close/delete a customer account."""
        # Create an account
        create_account(self.conn, "30005", "Delete Me", "7777", 200.0)
        deposit(self.conn, "30005", 100.0)

        # Confirm account and transactions exist
        bal = get_balance(self.conn, "30005")
        self.assertEqual(bal, 300.0)

        # Delete account
        res = delete_account(self.conn, "30005")
        self.assertTrue(res)

        # Confirm account is gone
        with self.assertRaises(AccountNotFoundException):
            get_balance(self.conn, "30005")

        with self.assertRaises(AccountNotFoundException):
            authenticate_user(self.conn, "30005", "7777")

    def test_delete_non_existent_account_raises_exception(self) -> None:
        """Verifies that deleting an invalid account raises AccountNotFoundException."""
        with self.assertRaises(AccountNotFoundException):
            delete_account(self.conn, "99999")


if __name__ == "__main__":
    unittest.main()
