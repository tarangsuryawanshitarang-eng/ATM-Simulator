"""
Database Seeder for the Advanced ATM Simulator.
Initializes tables via schema.sql and seeds 30 authentic Indian demo customer accounts
and physical cash vault cassettes.
"""

import sys
from pathlib import Path
from typing import Dict, List

# Support running directly as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from core.security import generate_salt, hash_pin
from database.connection import get_db_connection, immediate_transaction

# 30 Authentic Indian Demo Account Profiles
INDIAN_NAMES = [
    ("Tarang Suryawanshi", "1234", 2500.0, 0, 0),   # 10001 (Lead Developer)
    ("Sameep Patel", "4321", 1000.0, 0, 0),         # 10002 (Project Partner)
    ("Diya Iyer", "9999", 50.0, 0, 0),              # 10003
    ("Aditya Verma", "0000", 300.0, 1, 3),          # 10004 (Locked Demo)
    ("Aarav Sharma", "1111", 5000.0, 0, 0),         # 10005
    ("Vivaan Patel", "2222", 7500.0, 0, 0),         # 10006
    ("Ananya Gupta", "3333", 12000.0, 0, 0),        # 10007
    ("Rahul Deshmukh", "4444", 3200.0, 0, 0),       # 10008
    ("Sneha Joshi", "5555", 1500.0, 0, 0),          # 10009
    ("Priya Nair", "6666", 8900.0, 0, 0),           # 10010
    ("Rohan Mehta", "7777", 4500.0, 0, 0),          # 10011
    ("Vikram Singh", "8888", 6200.0, 0, 0),         # 10012
    ("Pooja Reddy", "1212", 2100.0, 0, 0),          # 10013
    ("Neha Kulkarni", "2323", 9400.0, 0, 0),        # 10014
    ("Arjun Rao", "3434", 11000.0, 0, 0),           # 10015
    ("Rajesh Kumar", "4545", 5300.0, 0, 0),         # 10016
    ("Sunita Devi", "5656", 1800.0, 0, 0),          # 10017
    ("Amit Shah", "6767", 14500.0, 0, 0),           # 10018
    ("Kavita Menon", "7878", 3700.0, 0, 0),         # 10019
    ("Suresh Raina", "8989", 16000.0, 0, 0),        # 10020
    ("Rohit Sharma", "4545", 25000.0, 0, 0),        # 10021
    ("Virat Kohli", "1818", 50000.0, 0, 0),         # 10022
    ("MS Dhoni", "0707", 45000.0, 0, 0),            # 10023
    ("Sachin Tendulkar", "1010", 35000.0, 0, 0),    # 10024
    ("Hardik Pandya", "3333", 22000.0, 0, 0),       # 10025
    ("Jasprit Bumrah", "9393", 28000.0, 0, 0),      # 10026
    ("Shubman Gill", "7777", 19000.0, 0, 0),        # 10027
    ("KL Rahul", "0101", 24000.0, 0, 0),            # 10028
    ("Rishabh Pant", "1717", 21000.0, 0, 0),        # 10029
    ("Sanju Samson", "1414", 13000.0, 0, 0),        # 10030
]

DEMO_ACCOUNTS: List[Dict] = [
    {
        "account_number": str(10001 + i),
        "account_holder": name,
        "pin": pin,
        "balance": bal,
        "is_locked": locked,
        "failed_attempts": failed,
    }
    for i, (name, pin, bal, locked, failed) in enumerate(INDIAN_NAMES)
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
    If reset=True, clears existing data before seeding 100 Indian customer accounts.
    If reset=False, only inserts demo records if they do not already exist,
    preserving all live customer account modifications, balances, and vault states.
    """
    init_database(db_path)
    conn = get_db_connection(db_path)
    try:
        with immediate_transaction(conn):
            if reset:
                conn.execute("DELETE FROM transactions;")
                conn.execute("DELETE FROM accounts;")
                conn.execute("DELETE FROM cash_vault;")

            # Seed 100 accounts
            for acc in DEMO_ACCOUNTS:
                salt = generate_salt()
                pin_hash = hash_pin(acc["pin"], salt)
                if reset:
                    conn.execute(
                        """
                        INSERT INTO accounts (account_number, account_holder, pin_hash, salt, balance, is_locked, failed_attempts)
                        VALUES (?, ?, ?, ?, ?, ?, ?);
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
                else:
                    conn.execute(
                        """
                        INSERT INTO accounts (account_number, account_holder, pin_hash, salt, balance, is_locked, failed_attempts)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(account_number) DO NOTHING;
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
                if reset:
                    conn.execute(
                        """
                        INSERT INTO cash_vault (denomination, note_count)
                        VALUES (?, ?);
                        """,
                        (denom, count),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO cash_vault (denomination, note_count)
                        VALUES (?, ?)
                        ON CONFLICT(denomination) DO NOTHING;
                        """,
                        (denom, count),
                    )
    finally:
        conn.close()


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    seed_data(reset=reset_flag)
    action = "reset and seeded" if reset_flag else "seeded (idempotent)"
    print(f"[+] Database {action} with 30 Indian customer accounts successfully at: {config.DB_PATH}")
