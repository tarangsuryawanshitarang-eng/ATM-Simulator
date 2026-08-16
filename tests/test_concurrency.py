"""
Concurrency & ACID Compliance Test Suite for the Advanced ATM Simulator.
Simulates race conditions, multi-threaded withdrawals, cassette depletion,
and concurrent balance synchronization to verify zero data anomalies.
"""

import concurrent.futures
import threading
import unittest
from pathlib import Path

from core.exceptions import (
    AtmCashExhaustedException,
    InsufficientFundsException,
)
from core.transaction import deposit, get_balance, withdraw
from core.vault import get_vault_inventory, replenish_vault
from database.connection import get_db_connection, immediate_transaction
from database.seeder import seed_data


class TestConcurrencySubsystem(unittest.TestCase):
    """ACID concurrency test suite simulating simultaneous multi-threaded operations."""

    def setUp(self) -> None:
        """Set up test database."""
        self.test_db_path = Path("test_concurrency_atm.db")
        seed_data(db_path=self.test_db_path, reset=True)

    def tearDown(self) -> None:
        """Clean up test database."""
        if self.test_db_path.exists():
            try:
                self.test_db_path.unlink()
            except PermissionError:
                pass

    def test_concurrent_withdrawal_overdraft_prevention(self) -> None:
        """
        Race condition simulation:
        Account starts with $500.00 balance.
        10 concurrent threads each attempt to withdraw $100.00 simultaneously.
        ACID Guarantee: Exactly 5 succeed, 5 fail. Final balance == $0.00.
        """
        account_num = "10001"
        initial_balance = 500.0

        # Set account balance to $500.00
        conn = get_db_connection(self.test_db_path)
        with immediate_transaction(conn):
            conn.execute("UPDATE accounts SET balance = ? WHERE account_number = ?;", (initial_balance, account_num))
            replenish_vault(conn, {500: 20, 200: 50, 100: 50})
        conn.close()

        success_count = 0
        insufficient_funds_count = 0
        other_errors = []
        lock = threading.Lock()

        def worker_withdraw() -> None:
            nonlocal success_count, insufficient_funds_count
            thread_conn = get_db_connection(self.test_db_path)
            try:
                withdraw(thread_conn, account_num, 100.0)
                with lock:
                    success_count += 1
            except InsufficientFundsException:
                with lock:
                    insufficient_funds_count += 1
            except Exception as e:
                with lock:
                    other_errors.append(str(e))
            finally:
                thread_conn.close()

        # Launch 10 worker threads simultaneously
        threads = [threading.Thread(target=worker_withdraw) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(other_errors), 0, f"Encountered unexpected concurrency errors: {other_errors}")
        self.assertEqual(success_count, 5, f"Expected exactly 5 successful withdrawals, got {success_count}")
        self.assertEqual(insufficient_funds_count, 5, f"Expected 5 insufficient funds exceptions, got {insufficient_funds_count}")

        # Check final balance in database
        final_conn = get_db_connection(self.test_db_path)
        final_balance = get_balance(final_conn, account_num)
        final_conn.close()

        self.assertEqual(final_balance, 0.0, f"Expected final balance to be exactly 0.0, got {final_balance}")

    def test_concurrent_cassette_exhaustion(self) -> None:
        """
        Vault cassette race condition simulation:
        Account has abundant balance ($5,000.00), but vault contains only two $500 notes ($1,000 total).
        6 concurrent threads each attempt to withdraw $500.00.
        ACID Guarantee: Exactly 2 succeed, 4 fail with AtmCashExhaustedException.
        """
        account_num = "10001"

        conn = get_db_connection(self.test_db_path)
        with immediate_transaction(conn):
            conn.execute("UPDATE accounts SET balance = 5000.0 WHERE account_number = ?;", (account_num,))
            replenish_vault(conn, {500: 2, 200: 0, 100: 0})
        conn.close()

        success_count = 0
        exhausted_count = 0
        other_errors = []
        lock = threading.Lock()

        def worker_withdraw_500() -> None:
            nonlocal success_count, exhausted_count
            thread_conn = get_db_connection(self.test_db_path)
            try:
                withdraw(thread_conn, account_num, 500.0)
                with lock:
                    success_count += 1
            except AtmCashExhaustedException:
                with lock:
                    exhausted_count += 1
            except Exception as e:
                with lock:
                    other_errors.append(str(e))
            finally:
                thread_conn.close()

        threads = [threading.Thread(target=worker_withdraw_500) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(other_errors), 0, f"Encountered unexpected errors: {other_errors}")
        self.assertEqual(success_count, 2, f"Expected 2 successful withdrawals, got {success_count}")
        self.assertEqual(exhausted_count, 4, f"Expected 4 cash exhausted exceptions, got {exhausted_count}")

        # Check vault state
        check_conn = get_db_connection(self.test_db_path)
        inv = get_vault_inventory(check_conn)
        final_balance = get_balance(check_conn, account_num)
        check_conn.close()

        self.assertEqual(inv[500], 0, "Vault $500 notes should be fully exhausted (0).")
        self.assertEqual(final_balance, 4000.0, "Account balance should have deducted exactly 2x$500 = $1,000.")

    def test_concurrent_mixed_deposits_and_withdrawals(self) -> None:
        """
        Simulates simultaneous deposits and withdrawals across multiple threads.
        Verifies mathematical balance consistency.
        """
        account_num = "10002"
        initial_balance = 1000.0

        conn = get_db_connection(self.test_db_path)
        with immediate_transaction(conn):
            conn.execute("UPDATE accounts SET balance = ? WHERE account_number = ?;", (initial_balance, account_num))
            replenish_vault(conn, {500: 50, 200: 50, 100: 50})
        conn.close()

        # 4 threads deposit $200 (1x$200 note) = +$800
        # 4 threads withdraw $100 = -$400
        # Expected net change = +$400 -> Expected final balance = $1,400.00

        def do_deposit() -> None:
            t_conn = get_db_connection(self.test_db_path)
            try:
                deposit(t_conn, account_num, {200: 1})
            finally:
                t_conn.close()

        def do_withdraw() -> None:
            t_conn = get_db_connection(self.test_db_path)
            try:
                withdraw(t_conn, account_num, 100.0)
            finally:
                t_conn.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for _ in range(4):
                futures.append(executor.submit(do_deposit))
            for _ in range(4):
                futures.append(executor.submit(do_withdraw))
            for f in concurrent.futures.as_completed(futures):
                f.result()  # Will re-raise if any exception occurred

        check_conn = get_db_connection(self.test_db_path)
        final_bal = get_balance(check_conn, account_num)
        check_conn.close()

        self.assertEqual(final_bal, 1400.0, f"Expected final balance $1400.00, got {final_bal}")


if __name__ == "__main__":
    unittest.main()
