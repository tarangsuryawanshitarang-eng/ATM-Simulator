"""
Thread-safe database connection provider and context manager for SQLite3.
Configures PRAGMA foreign_keys and PRAGMA busy_timeout on every connection.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Union

import config


def get_db_connection(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    """
    Creates and configures an SQLite3 connection.
    Enforces foreign keys, busy timeout, and row factory.
    Uses isolation_level=None to allow explicit manual transaction control
    (e.g., BEGIN IMMEDIATE TRANSACTION).
    """
    path = str(db_path or config.DB_PATH)
    conn = sqlite3.connect(
        path,
        timeout=config.BUSY_TIMEOUT_MS / 1000.0,
        isolation_level=None,  # Autocommit mode: enables explicit BEGIN IMMEDIATE
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row

    # Execute mandatory PRAGMAs on every connection
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute(f"PRAGMA busy_timeout = {config.BUSY_TIMEOUT_MS};")
    return conn


@contextmanager
def get_db_context(db_path: Optional[Union[str, Path]] = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager that yields an active SQLite connection and ensures it is closed.
    """
    conn = get_db_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def immediate_transaction(conn: sqlite3.Connection) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for atomic ACID transactions using BEGIN IMMEDIATE TRANSACTION.
    Guarantees an immediate write lock and rolls back on any exception.
    """
    conn.execute("BEGIN IMMEDIATE TRANSACTION;")
    try:
        yield conn
        conn.execute("COMMIT;")
    except Exception:
        conn.execute("ROLLBACK;")
        raise
