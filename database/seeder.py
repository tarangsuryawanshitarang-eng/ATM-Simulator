"""
Database Seeder for the Advanced ATM Simulator.
Initializes tables via schema.sql and seeds deterministic demo accounts and cash vault cassettes.
"""

import sys
from pathlib import Path

# Support running directly as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from core.security import generate_salt, hash_pin
from database.connection import get_db_connection, immediate_transaction


DEMO_ACCOUNTS = [
    {
        "account_number": "10001",
        "account_holder": "Alice Smith",
        "pin": "1234",
        "balance": 2500.0,
        "is_locked": 0,
        "failed_attempts": 0,
    },
    {
        "account_number": "10002",
        "account_holder": "Bob Jones",
        "pin": "4321",
        "balance": 1000.0,
        "is_locked": 0,
        "failed_attempts": 0,
    },
    {
        "account_number": "10003",
        "account_holder": "Charlie Brown",
        "pin": "9999",
        "balance": 50.0,
        "is_locked": 0,
        "failed_attempts": 0,
    },
    {
        "account_number": "10004",
        "account_holder": "Locked Account",
        "pin": "0000",
        "balance": 300.0,
        "is_locked": 1,
        "failed_attempts": 3,
    },
]


def init_database(db_path: Path = config.DB_PATH) -> None:
    """Creates tables and indexes from schema.sql if they do not already exist."""
    conn = get_db_connection(db_path)
    try:
        with open(config.SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
    finally:
        conn.close()


def seed_data(db_path: Path = config.DB_PATH, reset: bool = False) -> None:
    """
    Populates default demo accounts and cassette vault notes.
    If reset=True, clears existing data before seeding.
    """
    init_database(db_path)
    conn = get_db_connection(db_path)
    try:
        with immediate_transaction(conn):
            if reset:
                conn.execute("DELETE FROM transactions;")
                conn.execute("DELETE FROM accounts;")
                conn.execute("DELETE FROM cash_vault;")

            # Seed accounts
            for acc in DEMO_ACCOUNTS:
                salt = generate_salt()
                pin_hash = hash_pin(acc["pin"], salt)
                conn.execute(
                    """
                    INSERT INTO accounts (account_number, account_holder, pin_hash, salt, balance, is_locked, failed_attempts)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(account_number) DO UPDATE SET
                        account_holder = excluded.account_holder,
                        pin_hash = excluded.pin_hash,
                        salt = excluded.salt,
                        balance = excluded.balance,
                        is_locked = excluded.is_locked,
                        failed_attempts = excluded.failed_attempts;
                    """,
                    (
                        acc["account_number"],
                        acc["account_holder"],
                        pin_hash,
                        salt,
                        acc["balance"],
                        acc["is_locked"],
                        acc["failed_attempts"],
                    ),
                )

            # Seed vault cassettes
            for denom, count in config.DEFAULT_VAULT_INVENTORY.items():
                conn.execute(
                    """
                    INSERT INTO cash_vault (denomination, note_count)
                    VALUES (?, ?)
                    ON CONFLICT(denomination) DO UPDATE SET
                        note_count = excluded.note_count;
                    """,
                    (denom, count),
                )
    finally:
        conn.close()


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    print(f"[*] Initializing and seeding database at: {config.DB_PATH} (Reset={reset_flag})")
    seed_data(reset=reset_flag)
    print("[+] Database initialized successfully with demo accounts and vault cassettes.")
