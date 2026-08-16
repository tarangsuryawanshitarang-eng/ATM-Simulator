"""
SQLite3 Concrete Account Repository.
Implements IAccountRepository to map SQL records to domain Account entities.
"""

import sqlite3
from typing import List, Optional

from core.domain.account import Account
from core.exceptions import AccountAlreadyExistsException, AccountNotFoundException
from core.interfaces.repositories import IAccountRepository


class SqliteAccountRepository(IAccountRepository):
    """
    SQLite3 implementation of the Account Repository.
    Executes database operations using the provided connection within immediate transactions.
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_by_number(self, account_number: str) -> Optional[Account]:
        cursor = self.conn.execute(
            """
            SELECT account_number, account_holder, pin_hash, salt, balance, is_locked, failed_attempts, created_at
            FROM accounts
            WHERE account_number = ?;
            """,
            (str(account_number).strip(),),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Account(
            account_number=row["account_number"],
            account_holder=row["account_holder"],
            pin_hash=row["pin_hash"],
            salt=row["salt"],
            balance=float(row["balance"]),
            is_locked=bool(row["is_locked"]),
            failed_attempts=int(row["failed_attempts"]),
            created_at=row["created_at"],
        )

    def save(self, account: Account) -> None:
        cursor = self.conn.execute(
            """
            UPDATE accounts
            SET account_holder = ?,
                pin_hash = ?,
                salt = ?,
                balance = ?,
                is_locked = ?,
                failed_attempts = ?
            WHERE account_number = ?;
            """,
            (
                account.account_holder,
                account.pin_hash,
                account.salt,
                account.balance,
                1 if account.is_locked else 0,
                account.failed_attempts,
                account.account_number,
            ),
        )
        if cursor.rowcount == 0:
            raise AccountNotFoundException(f"Account '{account.account_number}' not found to update.")

    def create(self, account: Account) -> None:
        existing = self.get_by_number(account.account_number)
        if existing is not None:
            raise AccountAlreadyExistsException(
                f"Account number '{account.account_number}' already exists."
            )

        self.conn.execute(
            """
            INSERT INTO accounts (account_number, account_holder, pin_hash, salt, balance, is_locked, failed_attempts)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                account.account_number,
                account.account_holder,
                account.pin_hash,
                account.salt,
                account.balance,
                1 if account.is_locked else 0,
                account.failed_attempts,
            ),
        )

    def delete(self, account_number: str) -> bool:
        acc_num = str(account_number).strip()
        existing = self.get_by_number(acc_num)
        if existing is None:
            raise AccountNotFoundException(f"Account '{acc_num}' not found to delete.")

        # Clean up related transaction history records
        self.conn.execute(
            "DELETE FROM transactions WHERE account_number = ?;",
            (acc_num,),
        )
        # Delete the account entity record
        cursor = self.conn.execute(
            "DELETE FROM accounts WHERE account_number = ?;",
            (acc_num,),
        )
        return cursor.rowcount > 0

    def get_all(self) -> List[Account]:
        cursor = self.conn.execute(
            """
            SELECT account_number, account_holder, pin_hash, salt, balance, is_locked, failed_attempts, created_at
            FROM accounts
            ORDER BY account_number ASC;
            """
        )
        rows = cursor.fetchall()
        return [
            Account(
                account_number=row["account_number"],
                account_holder=row["account_holder"],
                pin_hash=row["pin_hash"],
                salt=row["salt"],
                balance=float(row["balance"]),
                is_locked=bool(row["is_locked"]),
                failed_attempts=int(row["failed_attempts"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def get_locked_accounts(self) -> List[Account]:
        cursor = self.conn.execute(
            """
            SELECT account_number, account_holder, pin_hash, salt, balance, is_locked, failed_attempts, created_at
            FROM accounts
            WHERE is_locked = 1
            ORDER BY account_number ASC;
            """
        )
        rows = cursor.fetchall()
        return [
            Account(
                account_number=row["account_number"],
                account_holder=row["account_holder"],
                pin_hash=row["pin_hash"],
                salt=row["salt"],
                balance=float(row["balance"]),
                is_locked=bool(row["is_locked"]),
                failed_attempts=int(row["failed_attempts"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def get_next_account_number(self) -> str:
        cursor = self.conn.execute(
            "SELECT account_number FROM accounts WHERE account_number GLOB '[0-9]*' ORDER BY CAST(account_number AS INTEGER) DESC LIMIT 1;"
        )
        row = cursor.fetchone()
        if row:
            try:
                return str(int(row["account_number"]) + 1)
            except ValueError:
                pass
        return "10001"
