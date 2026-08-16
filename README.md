# 🏧 Advanced ATM Simulator

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/Database-SQLite3-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite3"/>
  <img src="https://img.shields.io/badge/Transactions-ACID_Safe-success?style=for-the-badge" alt="ACID Safe"/>
  <img src="https://img.shields.io/badge/Security-PBKDF2--SHA256-red?style=for-the-badge" alt="PBKDF2-SHA256"/>
  <img src="https://img.shields.io/badge/Tests-16%20Passing%20(100%25)-brightgreen?style=for-the-badge" alt="Tests"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License"/>
</p>

<p align="center">
  <strong>A production-ready, transaction-safe Automated Teller Machine (ATM) simulation system engineered in Python and SQLite.</strong><br>
  Built with banking-grade PBKDF2 cryptography, exact-change cassette allocation algorithms, thread-safe ACID concurrency, and an interactive terminal interface.
</p>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Cassette & Denomination Allocation Algorithm](#-cassette--denomination-allocation-algorithm)
- [Security & Authentication Model](#-security--authentication-model)
- [Database Schema](#-database-schema)
- [Demo Accounts & Test Credentials](#-demo-accounts--test-credentials)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation & Virtual Environment](#installation--virtual-environment)
  - [Database Initialization](#database-initialization)
  - [Running the Application](#running-the-application)
- [Testing & Concurrency Verification](#-testing--concurrency-verification)
- [Project Directory Tree](#-project-directory-tree)
- [Contributing & License](#-contributing--license)

---

## 🌟 Overview

The **Advanced ATM Simulator** models real-world automated banking kiosks with institutional-grade rigor. It eliminates common simulator flaws (such as in-memory state loss, race condition overdrafts, naive greedy note dispensing failures, and plain-text PIN vulnerabilities) by providing:

1. **Deterministic Multi-Denomination Dispenser**: Solves exact physical currency note combinations (`$500`, `$200`, `$100`) using bounded backtracking.
2. **True ACID Transaction Safety**: Enforces `BEGIN IMMEDIATE TRANSACTION;` write locks and SQLite PRAGMA busy timeouts to guarantee zero balance inconsistencies during simultaneous multi-threaded operations.
3. **Cryptographic Protection**: Secures user PINs via **PBKDF2-HMAC-SHA256** (100,000 iterations), unique 16-byte random salts, timing-safe constant-time comparisons, and automatic 3-strike brute-force lockouts.
4. **Comprehensive Audit Trails**: Persistently records every authentication attempt, balance inquiry, deposit, withdrawal, and lockout in an immutable transaction ledger.

---

## ✨ Key Features

| Category | Capability | Technical Implementation |
|:---|:---|:---|
| 🔒 **Security** | **PBKDF2-HMAC-SHA256** | 100,000 hash rounds + 16-byte cryptographic salt via `secrets` module |
| 🛡️ **Anti-Tamper** | **Timing-Safe Verification** | Constant-time digest comparison via `secrets.compare_digest` |
| 🚫 **Protection** | **Brute-Force Lockout** | Immediate account locking upon 3 consecutive failed PIN attempts |
| ⚡ **Concurrency** | **ACID Guarantees** | `BEGIN IMMEDIATE TRANSACTION;` preventing write-lock collisions & race conditions |
| 💵 **Dispenser** | **Bounded Note Allocator** | Exact-change backtracking solver across physical note cassettes (`$500`, `$200`, `$100`) |
| 📜 **Auditability** | **Relational Ledger** | Full audit trail (`AUTHENTICATE`, `BALANCE_INQUIRY`, `WITHDRAWAL`, `DEPOSIT`, `LOCKOUT`) |
| 🖥️ **CLI Experience** | **Interactive Terminal** | Rich ANSI styling, fast cash buttons, custom deposits, statements, and admin tools |

---

## 🏛️ System Architecture

```
                                  ┌──────────────────────────────────┐
                                  │      Terminal CLI Interface      │
                                  │            (main.py)             │
                                  └────────────────┬─────────────────┘
                                                   │
                         ┌─────────────────────────┴────────────────────────┐
                         │                                                  │
                         ▼                                                  ▼
         ┌───────────────────────────────┐                  ┌───────────────────────────────┐
         │       Security Engine         │                  │      Transaction Engine       │
         │      (core/security.py)       │                  │     (core/transaction.py)     │
         │ • PBKDF2-HMAC-SHA256 (100k)   │                  │ • BEGIN IMMEDIATE TX (ACID)   │
         │ • 16-Byte Cryptographic Salts │                  │ • Atomic Balance Transitions  │
         │ • Constant-Time Comparison    │                  │ • Comprehensive Audit Logging │
         │ • 3-Attempt Lockout Enforcer  │                  └───────────────┬───────────────┘
         └───────────────┬───────────────┘                                  │
                         │                                                  │
                         │                                                  ▼
                         │                                  ┌───────────────────────────────┐
                         │                                  │    Vault Cassette Manager     │
                         │                                  │        (core/vault.py)        │
                         │                                  │ • Backtracking Note Solver    │
                         │                                  │ • Physical Note Deductions    │
                         │                                  │ • Exact Change Verification   │
                         │                                  └───────────────┬───────────────┘
                         │                                                  │
                         └─────────────────────────┬────────────────────────┘
                                                   │
                                                   ▼
                                  ┌──────────────────────────────────┐
                                  │   SQLite3 Relational Backend     │
                                  │     (database/connection.py)     │
                                  │ • PRAGMA foreign_keys = ON       │
                                  │ • PRAGMA busy_timeout = 5000     │
                                  │ • Idempotent schema.sql          │
                                  └──────────────────────────────────┘
```

---

## 💵 Cassette & Denomination Allocation Algorithm

Traditional ATM simulations use a **greedy** dispenser (taking the highest note first). Greedy approaches fail in bounded inventory scenarios:

> **Example Failure in Greedy Solvers:**  
> - Vault has: `1 x $500`, `3 x $200`, `0 x $100`  
> - Requested amount: `$600`  
> - *Greedy Solver:* Takes `1 x $500` -> Remaining `$100` -> **Fails** (No `$100` notes available).  
> - *Our Backtracking Solver:* Evaluates `$500`, detects dead end, backtracks and dispenses `3 x $200` = `$600` -> **Success!**

```
Withdrawal Request ($Amount)
            │
            ▼
 [Divisible by $100?] ─── NO ───► Raise UnsupportedDenominationException
            │ YES
            ▼
 [Sufficient Total Cash?] ── NO ──► Raise AtmCashExhaustedException
            │ YES
            ▼
 [Exact Change Backtracker]
   ├── Try max $500 notes ──► Check remaining
   ├── Try max $200 notes ──► Check remaining
   └── Try max $100 notes ──► Exact match found?
            │
            ├── Found ──► Atomic Deduct from Cassettes ($500, $200, $100)
            └── None  ──► Raise AtmCashExhaustedException ("Cannot dispense exact change")
```

---

## 🔒 Security & Authentication Model

1. **PIN Derivation**:
   $$\text{pin\_hash} = \text{PBKDF2-HMAC-SHA256}(\text{PIN}, \text{salt}, \text{iterations}=100000)$$
2. **Salt Generation**: Cryptographically secure 16-byte random hex string (`secrets.token_hex(16)`), ensuring each user has a unique salt.
3. **Constant-Time Verification**: Prevents side-channel timing attacks by using `secrets.compare_digest()`.
4. **Lockout Policy**: Tracks `failed_attempts`. Upon 3 consecutive failures:
   - Account is locked (`is_locked = 1`).
   - A `LOCKOUT` audit transaction is committed.
   - All further attempts (even with the correct PIN) are rejected until unlocked by an administrator.

---

## 🗄️ Database Schema

The database utilizes SQLite with strict constraints and foreign keys (`PRAGMA foreign_keys = ON;`):

### `accounts`
| Column | Type | Constraints | Description |
|:---|:---|:---|:---|
| `account_number` | `TEXT` | `PRIMARY KEY` | Unique account identifier |
| `account_holder` | `TEXT` | `NOT NULL` | Customer full name |
| `pin_hash` | `TEXT` | `NOT NULL` | PBKDF2 derived key hex string |
| `salt` | `TEXT` | `NOT NULL` | 16-byte random cryptographic salt |
| `balance` | `REAL` | `NOT NULL CHECK (balance >= 0.0)` | Non-negative account balance |
| `is_locked` | `INTEGER` | `NOT NULL CHECK (is_locked IN (0, 1))` | Lock status flag |
| `failed_attempts` | `INTEGER` | `NOT NULL CHECK (failed_attempts >= 0)` | Consecutive failed PIN counter |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | Account creation timestamp |

### `transactions`
| Column | Type | Constraints | Description |
|:---|:---|:---|:---|
| `transaction_id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Unique transaction ID |
| `account_number` | `TEXT` | `FOREIGN KEY REFERENCES accounts` | Associated account |
| `transaction_type` | `TEXT` | `CHECK (IN 'AUTHENTICATE', 'BALANCE_INQUIRY', 'WITHDRAWAL', 'DEPOSIT', 'LOCKOUT')` | Transaction classification |
| `amount` | `REAL` | `NOT NULL DEFAULT 0.0` | Transaction monetary value |
| `status` | `TEXT` | `CHECK (IN 'SUCCESS', 'FAILED', 'REJECTED')` | Final state of operation |
| `failure_reason` | `TEXT` | `NULLABLE` | Reason code on failure/rejection |
| `timestamp` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | Audit event timestamp |

### `cash_vault`
| Column | Type | Constraints | Description |
|:---|:---|:---|:---|
| `denomination` | `INTEGER` | `PRIMARY KEY CHECK (IN (500, 200, 100))` | Note value ($) |
| `note_count` | `INTEGER` | `NOT NULL CHECK (note_count >= 0)` | Physical notes in cassette |

---

## 👥 Demo Accounts & Test Credentials

The database seeder pre-configures test profiles:

| Account Number | Account Holder  | PIN    | Initial Balance | Status | Note |
|:---|:---|:---|:---|:---|:---|
| `10001` | **Alice Smith** | `1234` | `$2,500.00` | Active | Standard customer |
| `10002` | **Bob Jones** | `4321` | `$1,000.00` | Active | Used for lockout tests |
| `10003` | **Charlie Brown** | `9999` | `$50.00` | Active | Low balance account |
| `10004` | **Locked User** | `0000` | `$300.00` | **Locked** | Pre-locked demo account |

**Initial Vault Cassette Cash**:
- `$500` Cassette: 20 notes (`$10,000.00`)
- `$200` Cassette: 50 notes (`$10,000.00`)
- `$100` Cassette: 100 notes (`$10,000.00`)
- **Total Physical Cash in ATM**: **`$30,000.00`**

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10** or higher
- Git

### Installation & Virtual Environment

1. **Clone the repository**:
   ```bash
   git clone <YOUR_REPOSITORY_URL>
   cd atm-simulator
   ```

2. **Create and activate a virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD)**:
     ```cmd
     python -m venv .venv
     .\.venv\Scripts\activate.bat
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Database Initialization

Initialize database tables and seed test accounts and vault cassettes:
```bash
python database/seeder.py --reset
```

### Running the Application

- **Customer ATM Kiosk (Default)**:
  ```bash
  python main.py
  ```
  Launches the real-world cardholder interface (Login, Balance, Withdraw, Deposit, Statement, Change PIN).

- **Bank Manager / Admin Control Panel**:
  ```bash
  python admin.py
  ```
  Launches the dedicated Bank Manager dashboard to inspect customer accounts and balances in SQL tables (without exposing customer PINs), manage vault cassettes, unlock accounts, and view global audit logs.


---

## 🧪 Testing & Concurrency Verification

The test suite thoroughly verifies security, cash allocation, and multi-threaded ACID guarantees.

Run all tests inside your virtual environment:
```bash
# Using pytest
pytest tests/ -v

# OR using standard library unittest
python -m unittest discover -s tests -v
```

### Test Coverage Highlights

- **`test_security.py`**:
  - Validates salt entropy and PBKDF2 hash uniqueness.
  - Tests constant-time PIN comparison.
  - Simulates brute-force attack: confirms failed attempt incrementing and hard lockout at attempt 3.
  - Verifies reset of failed attempt counter on valid login.
- **`test_vault.py`**:
  - Tests greedy and backtracking exact-change denomination solutions.
  - Verifies `AtmCashExhaustedException` and `UnsupportedDenominationException`.
  - Tests cassette inventory state transitions during deposits and withdrawals.
- **`test_concurrency.py`**:
  - **Overdraft Race Condition Prevention**: Simulates 10 threads concurrently attempting to withdraw from a $500 account; confirms exactly 5 succeed and 5 fail, yielding a final balance of exactly $0.00 (zero negative balance anomalies).
  - **Cassette Exhaustion Concurrency**: Verifies safe note deductions when parallel withdrawals contend for the same physical cassette notes.
  - **Mixed Operations**: Confirms mathematical consistency under simultaneous deposits and withdrawals across worker threads.

---

## 📁 Project Directory Tree

```text
atm-simulator/
├── .gitignore              # Ignores .venv, cache, and db files
├── README.md               # Architecture, manuals & technical documentation
├── requirements.txt        # Minimal test dependencies (pytest)
├── main.py                 # Customer ATM terminal interface (Default)
├── admin.py                # Bank Manager / Administrator dashboard
├── config.py               # Centralized configuration & constants
├── database/
│   ├── __init__.py
│   ├── connection.py       # Thread-safe SQLite connection factory & PRAGMAs
│   ├── schema.sql          # Relational DDL with strict integrity constraints
│   └── seeder.py           # Database seeder for demo accounts & cassettes
├── core/
│   ├── __init__.py
│   ├── exceptions.py       # Domain-specific custom exception hierarchy
│   ├── security.py         # PBKDF2 cryptography & lockout management
│   ├── vault.py            # Backtracking denomination solver & cassette inventory
│   └── transaction.py      # ACID transaction coordinator (BEGIN IMMEDIATE)
└── tests/
    ├── __init__.py
    ├── test_security.py    # Unit tests for security & lockout
    ├── test_vault.py       # Unit tests for note allocation & cash exhaustion
    └── test_concurrency.py # ACID concurrency & race condition test suite
```

---

## 📄 License

This project is distributed under the **MIT License**. Feel free to use, modify, and distribute for educational or commercial purposes.
