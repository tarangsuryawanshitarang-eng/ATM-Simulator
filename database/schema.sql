-- Idempotent Database Schema for Advanced ATM Simulator
-- Enforces strict relational integrity and table constraints.

CREATE TABLE IF NOT EXISTS accounts (
    account_number TEXT PRIMARY KEY,
    account_holder TEXT NOT NULL,
    pin_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    balance REAL NOT NULL DEFAULT 0.0 CHECK (balance >= 0.0),
    is_locked INTEGER NOT NULL DEFAULT 0 CHECK (is_locked IN (0, 1)),
    failed_attempts INTEGER NOT NULL DEFAULT 0 CHECK (failed_attempts >= 0),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_number TEXT NOT NULL,
    transaction_type TEXT NOT NULL CHECK (
        transaction_type IN ('AUTHENTICATE', 'BALANCE_INQUIRY', 'WITHDRAWAL', 'DEPOSIT', 'LOCKOUT')
    ),
    amount REAL NOT NULL DEFAULT 0.0 CHECK (amount >= 0.0),
    status TEXT NOT NULL CHECK (
        status IN ('SUCCESS', 'FAILED', 'REJECTED')
    ),
    failure_reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_number) REFERENCES accounts (account_number) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS cash_vault (
    denomination INTEGER PRIMARY KEY CHECK (denomination IN (500, 200, 100)),
    note_count INTEGER NOT NULL CHECK (note_count >= 0)
);

-- Performance and query indexes
CREATE INDEX IF NOT EXISTS idx_transactions_account_timestamp 
ON transactions (account_number, timestamp DESC);
