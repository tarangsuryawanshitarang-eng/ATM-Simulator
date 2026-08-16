"""
Global configuration constants for the Advanced ATM Simulator.
Defines security parameters, database locations, supported denominations, and business limits.
"""

from pathlib import Path

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DB_PATH = BASE_DIR / "atm.db"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"

# Cryptographic & Security Parameters
PBKDF2_HASH_NAME = "sha256"
PBKDF2_ITERATIONS = 100_000
SALT_BYTE_LENGTH = 16
MAX_FAILED_ATTEMPTS = 3

# Vault & Cassette Parameters
SUPPORTED_DENOMINATIONS = (500, 200, 100)
DEFAULT_VAULT_INVENTORY = {
    500: 20,  # 20 * $500 = $10,000
    200: 50,  # 50 * $200 = $10,000
    100: 100, # 100 * $100 = $10,000
}             # Total = $30,000

# SQLite Concurrency & Pragma Settings
BUSY_TIMEOUT_MS = 5000
FOREIGN_KEYS_ENABLED = True
