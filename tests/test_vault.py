"""
Unit Tests for Vault & Cassette Denomination Allocation Subsystem.
Tests bounded knapsack / backtracking allocation, greedy fallbacks, cash exhaustion, and deposit accounting.
"""

import sqlite3
import unittest
from pathlib import Path

from core.exceptions import (
    AtmCashExhaustedException,
    InvalidAmountException,
    UnsupportedDenominationException,
)
from core.vault import (
    deposit_notes,
    dispense_cash,
    get_total_vault_cash,
    get_vault_inventory,
    replenish_vault,
    solve_denomination_allocation,
)
from database.connection import get_db_connection, immediate_transaction
from database.seeder import seed_data


class TestVaultSubsystem(unittest.TestCase):
    """Test suite for cash dispenser algorithms and physical cassette states."""

    def setUp(self) -> None:
        """Initialize temporary database."""
        self.test_db_path = Path("test_vault_atm.db")
        seed_data(db_path=self.test_db_path, reset=True)
        self.conn = get_db_connection(self.test_db_path)

    def tearDown(self) -> None:
        """Close connection and clean up."""
        self.conn.close()
        if self.test_db_path.exists():
            try:
                self.test_db_path.unlink()
            except PermissionError:
                pass

    def test_greedy_denomination_allocation(self) -> None:
        """Verifies standard greedy note allocation when all note types are abundant."""
        inventory = {500: 10, 200: 10, 100: 10}
        # $800 = 1x500 + 1x200 + 1x100
        alloc = solve_denomination_allocation(800, inventory)
        self.assertEqual(alloc, {500: 1, 200: 1, 100: 1})

        # $1500 = 3x500
        alloc2 = solve_denomination_allocation(1500, inventory)
        self.assertEqual(alloc2, {500: 3})

        # $700 = 1x500 + 1x200
        alloc3 = solve_denomination_allocation(700, inventory)
        self.assertEqual(alloc3, {500: 1, 200: 1})

    def test_backtracking_non_greedy_allocation(self) -> None:
        """
        Verifies exact change calculation where a naive greedy approach would fail.
        Case 1: Target $600 with inventory {500: 1, 200: 3, 100: 0}.
        Greedy takes 1x500, remaining 100 fails. Backtracking finds 3x200 = 600.
        """
        inventory = {500: 1, 200: 3, 100: 0}
        alloc = solve_denomination_allocation(600, inventory)
        self.assertEqual(alloc, {200: 3})

        # Case 2: Target $1,100 with inventory {500: 2, 200: 3, 100: 0}.
        # 2x500 = 1000 (leaves 100 -> fails). Backtracking takes 1x500 + 3x200 = 1100.
        inventory2 = {500: 2, 200: 3, 100: 0}
        alloc2 = solve_denomination_allocation(1100, inventory2)
        self.assertEqual(alloc2, {500: 1, 200: 3})

    def test_cash_exhaustion_exception(self) -> None:
        """Verifies AtmCashExhaustedException when vault total cash is insufficient."""
        inventory = {500: 1, 200: 1, 100: 1}  # Total $800
        with self.assertRaises(AtmCashExhaustedException):
            solve_denomination_allocation(900, inventory)

    def test_unsupported_denomination_exception(self) -> None:
        """Verifies UnsupportedDenominationException for non-multiples of minimum note ($100)."""
        inventory = {500: 10, 200: 10, 100: 10}
        with self.assertRaises(UnsupportedDenominationException):
            solve_denomination_allocation(250, inventory)
        with self.assertRaises(UnsupportedDenominationException):
            solve_denomination_allocation(75, inventory)

    def test_invalid_amount_exception(self) -> None:
        """Verifies InvalidAmountException for zero, negative, or invalid amounts."""
        inventory = {500: 10, 200: 10, 100: 10}
        with self.assertRaises(InvalidAmountException):
            solve_denomination_allocation(0, inventory)
        with self.assertRaises(InvalidAmountException):
            solve_denomination_allocation(-500, inventory)

    def test_physical_cash_dispense_and_db_update(self) -> None:
        """Verifies that dispensing cash deducts the physical notes from the SQLite table."""
        with immediate_transaction(self.conn):
            # Seed custom inventory: 500: 2, 200: 5, 100: 5 (Total: 1000 + 1000 + 500 = $2,500)
            replenish_vault(self.conn, {500: 2, 200: 5, 100: 5})

        with immediate_transaction(self.conn):
            # Dispense $700 -> 1x500, 1x200
            alloc = dispense_cash(self.conn, 700)
            self.assertEqual(alloc, {500: 1, 200: 1})

        # Verify updated counts in DB
        inv = get_vault_inventory(self.conn)
        self.assertEqual(inv[500], 1)
        self.assertEqual(inv[200], 4)
        self.assertEqual(inv[100], 5)
        self.assertEqual(get_total_vault_cash(self.conn), 1800)

    def test_physical_cash_deposit_and_db_update(self) -> None:
        """Verifies depositing physical notes increments cassette note counts."""
        with immediate_transaction(self.conn):
            replenish_vault(self.conn, {500: 10, 200: 10, 100: 10})

        with immediate_transaction(self.conn):
            # Deposit 2x$500, 3x$200, 4x$100 = 1000 + 600 + 400 = $2,000
            total_value = deposit_notes(self.conn, {500: 2, 200: 3, 100: 4})
            self.assertEqual(total_value, 2000)

        inv = get_vault_inventory(self.conn)
        self.assertEqual(inv[500], 12)
        self.assertEqual(inv[200], 13)
        self.assertEqual(inv[100], 14)


if __name__ == "__main__":
    unittest.main()
