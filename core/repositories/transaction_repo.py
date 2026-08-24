"""
SQLite3 Concrete Transaction Repository.
Implements ITransactionRepository to manage audit trail persistence.
"""

import sqlite3
from typing import List, Optional

from core.domain.transaction import TransactionRecord
from core.interfaces.repositories import ITransactionRepository


class SqliteTransactionRepository(ITransactionRepository):
    """
    SQLite3 implementation of the Transaction Repository.
    Inserts immutable audit logs and queries recent activity.
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def record_transaction(self, tx: TransactionRecord) -> int:
        cursor = self.conn.execute(
            """
            INSERT INTO transactions (account_number, transaction_type, amount, status, failure_reason)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                tx.account_number,
                tx.transaction_type,
                float(tx.amount),
                tx.status,
                tx.failure_reason,
            ),
        )
        return cursor.lastrowid or 0

    def get_recent_by_account(
        self, account_number: str, limit: int = 10
    ) -> List[TransactionRecord]:
        cursor = self.conn.execute(
            """
            SELECT transaction_id, account_number, transaction_type, amount, status, failure_reason, timestamp
            FROM transactions
            WHERE account_number = ?
            ORDER BY timestamp DESC, transaction_id DESC
            LIMIT ?;
            """,
            (str(account_number).strip(), limit),
        )
        rows = cursor.fetchall()
        return [
            TransactionRecord(
                transaction_id=row["transaction_id"],
                account_number=row["account_number"],
                transaction_type=row["transaction_type"],
                amount=float(row["amount"]),
                status=row["status"],
                failure_reason=row["failure_reason"],
                timestamp=row["timestamp"],
            )
            for row in rows
        ]

    def get_global_audit_logs(
        self, tx_type: Optional[str] = None, limit: int = 25
    ) -> List[TransactionRecord]:
        if tx_type:
            cursor = self.conn.execute(
                """
                SELECT transaction_id, account_number, transaction_type, amount, status, failure_reason, timestamp
                FROM transactions
                WHERE transaction_type = ?
                ORDER BY transaction_id DESC
                LIMIT ?;
                """,
                (tx_type, limit),
            )
        else:
            cursor = self.conn.execute(
                """
                SELECT transaction_id, account_number, transaction_type, amount, status, failure_reason, timestamp
                FROM transactions
                ORDER BY transaction_id DESC
                LIMIT ?;
                """,
                (limit,),
            )

        rows = cursor.fetchall()
        return [
            TransactionRecord(
                transaction_id=row["transaction_id"],
                account_number=row["account_number"],
                transaction_type=row["transaction_type"],
                amount=float(row["amount"]),
                status=row["status"],
                failure_reason=row["failure_reason"],
                timestamp=row["timestamp"],
            )
            for row in rows
        ]
