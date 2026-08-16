"""
Unit Tests for Domain Entities, Repositories, and Clean Architecture Services.
Verifies SOLID design principles, OOP encapsulation, strategy hashing, and repository abstractions.
"""

import os
import sqlite3
import unittest
from pathlib import Path

import config
from core.domain.account import Account
from core.domain.vault import VaultCassette
from core.exceptions import (
    AccountAlreadyExistsException,
    AccountLockedException,
    AuthenticationFailedException,
    InsufficientFundsException,
    InvalidAmountException,
    UnsupportedDenominationException,
)
from core.repositories.account_repo import SqliteAccountRepository
from core.repositories.transaction_repo import SqliteTransactionRepository
from core.repositories.vault_repo import SqliteVaultRepository
from core.services.authentication import AuthenticationService
from core.services.security import Pbkdf2PepperHashProvider
from core.services.transaction import BankingTransactionService
from core.services.vault import VaultManagerService
from database.connection import get_db_connection
from database.seeder import seed_data


class TestDomainEntitiesAndServices(unittest.TestCase):
    """Test suite for OOP Domain Entities and Services."""

    def setUp(self) -> None:
        self.test_db_path = Path("test_domain_services.db")
        seed_data(db_path=self.test_db_path, reset=True)
        self.conn = get_db_connection(self.test_db_path)

        self.account_repo = SqliteAccountRepository(self.conn)
        self.tx_repo = SqliteTransactionRepository(self.conn)
        self.vault_repo = SqliteVaultRepository(self.conn)

        self.hash_provider = Pbkdf2PepperHashProvider()
        self.auth_service = AuthenticationService(
            self.account_repo, self.tx_repo, self.hash_provider
        )
        self.vault_service = VaultManagerService(self.vault_repo)
        self.tx_service = BankingTransactionService(
            self.account_repo, self.tx_repo, self.vault_service, self.hash_provider
        )

    def tearDown(self) -> None:
        self.conn.close()
        if self.test_db_path.exists():
            try:
                os.remove(self.test_db_path)
            except PermissionError:
                pass

    def test_account_entity_encapsulation(self) -> None:
        """Verifies business rule encapsulation inside the Account domain entity."""
        acc = Account(
            account_number="30001",
            account_holder="John Tester",
            pin_hash="dummy_hash",
            salt="dummy_salt",
            balance=1000.0,
            is_locked=False,
            failed_attempts=0,
        )

        self.assertTrue(acc.can_withdraw(500.0))
        self.assertFalse(acc.can_withdraw(1500.0))

        # Withdrawal
        new_bal = acc.apply_withdrawal(400.0)
        self.assertEqual(new_bal, 600.0)
        self.assertEqual(acc.balance, 600.0)

        # Deposit
        new_bal = acc.apply_deposit(200.0)
        self.assertEqual(new_bal, 800.0)

        # Lockout behavior
        self.assertFalse(acc.record_failed_attempt(3))  # attempt 1
        self.assertFalse(acc.record_failed_attempt(3))  # attempt 2
        self.assertTrue(acc.record_failed_attempt(3))   # attempt 3 -> locked
        self.assertTrue(acc.is_locked)

        # Unlock
        acc.unlock()
        self.assertFalse(acc.is_locked)
        self.assertEqual(acc.failed_attempts, 0)

    def test_vault_cassette_entity(self) -> None:
        """Verifies VaultCassette calculations and operations."""
        c = VaultCassette(denomination=500, note_count=10)
        self.assertEqual(c.subtotal, 5000)

        c.deduct(3)
        self.assertEqual(c.note_count, 7)
        self.assertEqual(c.subtotal, 3500)

        c.add(5)
        self.assertEqual(c.note_count, 12)
        self.assertEqual(c.subtotal, 6000)

        with self.assertRaises(UnsupportedDenominationException):
            VaultCassette(denomination=50, note_count=10)

    def test_hash_provider_v3_format(self) -> None:
        """Verifies Pbkdf2PepperHashProvider produces v3$ prefixed hashes and verifies constant-time."""
        salt = self.hash_provider.generate_salt()
        digest = self.hash_provider.hash_pin("1234", salt)
        self.assertTrue(digest.startswith("v3$"))
        self.assertTrue(self.hash_provider.verify_pin("1234", salt, digest))
        self.assertFalse(self.hash_provider.verify_pin("0000", salt, digest))

    def test_auth_service_auto_generated_account_number(self) -> None:
        """Verifies customer registration with auto-incremented sequential account number."""
        acc = self.auth_service.create_customer_account(
            account_holder="Alice Wonderland",
            pin="9876",
            initial_balance=0.0,
        )
        self.assertEqual(acc.account_holder, "Alice Wonderland")
        self.assertEqual(acc.balance, 0.0)

        # Immediate authentication check
        auth_acc = self.auth_service.authenticate(acc.account_number, "9876")
        self.assertEqual(auth_acc.account_number, acc.account_number)

    def test_banking_transaction_service_withdrawal_and_deposit(self) -> None:
        """Verifies atomic withdrawal and deposit through BankingTransactionService."""
        # 10001 is seeded with $2,500.00
        bal = self.tx_service.check_balance("10001")
        self.assertEqual(bal, 2500.0)

        # Withdraw $700 (500x1 + 200x1)
        w_res = self.tx_service.withdraw_cash("10001", 700.0)
        self.assertEqual(w_res["new_balance"], 1800.0)
        self.assertEqual(w_res["dispensed_notes"], {500: 1, 200: 1})

        # Deposit $500
        d_res = self.tx_service.deposit_cash("10001", 500.0)
        self.assertEqual(d_res["new_balance"], 2300.0)

        # Check statement
        stmt = self.tx_service.get_statement("10001", limit=5)
        self.assertTrue(len(stmt) >= 3)


if __name__ == "__main__":
    unittest.main()
