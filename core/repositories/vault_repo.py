"""
SQLite3 Concrete Vault Repository.
Implements IVaultRepository for managing cassette inventory persistence.
"""

import sqlite3
from typing import Dict

import config
from core.domain.vault import VaultCassette
from core.interfaces.repositories import IVaultRepository


class SqliteVaultRepository(IVaultRepository):
    """
    SQLite3 implementation of the Vault Repository.
    Synchronizes physical cassette state with the cash_vault table.
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_all_cassettes(self) -> Dict[int, VaultCassette]:
        cursor = self.conn.execute(
            "SELECT denomination, note_count FROM cash_vault ORDER BY denomination DESC;"
        )
        rows = cursor.fetchall()
        cassettes = {
            row["denomination"]: VaultCassette(
                denomination=row["denomination"], note_count=row["note_count"]
            )
            for row in rows
        }

        # Ensure all supported denominations exist
        for denom in config.SUPPORTED_DENOMINATIONS:
            if denom not in cassettes:
                cassettes[denom] = VaultCassette(denomination=denom, note_count=0)

        return cassettes

    def save_inventory(self, inventory: Dict[int, int]) -> None:
        for denom, count in inventory.items():
            self.conn.execute(
                """
                UPDATE cash_vault
                SET note_count = ?
                WHERE denomination = ?;
                """,
                (count, denom),
            )

    def replenish(self, refill: Dict[int, int]) -> None:
        for denom, count in refill.items():
            if denom in config.SUPPORTED_DENOMINATIONS and count >= 0:
                self.conn.execute(
                    """
                    INSERT INTO cash_vault (denomination, note_count)
                    VALUES (?, ?)
                    ON CONFLICT(denomination) DO UPDATE SET note_count = excluded.note_count;
                    """,
                    (denom, count),
                )
