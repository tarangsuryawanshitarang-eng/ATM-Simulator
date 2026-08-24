# 🏧 Advanced ATM Simulator

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/Database-SQLite3-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite3"/>
  <img src="https://img.shields.io/badge/Transactions-ACID_Safe-success?style=for-the-badge" alt="ACID Safe"/>
  <img src="https://img.shields.io/badge/Security-PBKDF2--SHA256--Pepper-red?style=for-the-badge" alt="PBKDF2-SHA256-Pepper"/>
  <img src="https://img.shields.io/badge/UI-24--bit_TrueColor_TUI-cyan?style=for-the-badge" alt="TrueColor TUI"/>
  <img src="https://img.shields.io/badge/Architecture-SOLID_Clean_Design-purple?style=for-the-badge" alt="SOLID Clean Design"/>
  <img src="https://img.shields.io/badge/Tests-32%20Passing%20(100%25)-brightgreen?style=for-the-badge" alt="Tests"/>
</p>

<p align="center">
  <strong>An institutional-grade, transaction-safe Automated Teller Machine (ATM) simulation system engineered in Python and SQLite.</strong><br>
  Featuring a cutting-edge 24-bit TrueColor Terminal User Interface (TUI), clean Object-Oriented SOLID architecture, 30 customer demo accounts, real-time masked PIN entry, live cash dispensing animations, authentic thermal paper receipts, and banking-grade PBKDF2 cryptography with HMAC Pepper defense.
</p>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Security & Cryptographic Model](#-security--cryptographic-model)
- [Cash Dispenser Algorithm](#-cash-dispenser-algorithm)
- [Database Schema & ACID Transactions](#-database-schema--acid-transactions)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation & Setup](#installation--setup)
  - [Database Initialization](#database-initialization)
  - [Running the Customer ATM Kiosk](#running-the-customer-atm-kiosk)
  - [Running the Bank Manager Portal](#running-the-bank-manager-portal)
- [Testing Suite](#-testing-suite)
- [Project Directory Structure](#-project-directory-structure)

---

## 🌟 Overview

The **Advanced ATM Simulator** models real-world automated banking kiosks with institutional-grade engineering rigor and visually stunning terminal aesthetics.

### ✨ Core Capabilities:
1. **24-bit TrueColor Terminal Interface**: High-resolution RGB gradients, cardholder dashboard widgets, status badges, and interactive thermal receipts.
2. **Interactive Micro-Animations**: EMV chip reading simulations, motorized note counting dispenser, and optical vault deposit intake animations.
3. **Real-Time Masked PIN Input**: Real-time bullet masking (`●●●●`) with backspace support across Windows and POSIX terminals.
4. **Deterministic Multi-Denomination Dispenser**: Solves exact physical currency note combinations (`$500`, `$200`, `$100`) using bounded backtracking.
5. **True ACID Transaction Safety**: Enforces `BEGIN IMMEDIATE TRANSACTION;` write locks and SQLite PRAGMA busy timeouts to guarantee zero balance inconsistencies during simultaneous multi-threaded operations.
6. **Cryptographic Protection**: Secures user PINs via **PBKDF2-HMAC-SHA256** (100,000 iterations), unique 16-byte random salts, server-side HMAC secret pepper defense, timing-safe constant-time comparisons, and automatic 3-strike brute-force lockouts.
7. **Clean Architecture & SOLID Design**: Strict separation across Domain Entities (`Account`, `VaultCassette`), Abstract Interfaces (`IAccountRepository`, `IAuthenticationService`), Data Access Repositories (`SqliteAccountRepository`), and Domain Services (`BankingTransactionService`, `VaultManagerService`).

---

## 🎯 Key Features

| Category | Capability | Technical Implementation |
|:---|:---|:---|
| 🎨 **Terminal UI** | **24-bit TrueColor TUI** | RGB Linear Gradients, Unicode Box Sets, Glowing Status Badges |
| 🎬 **Animations** | **Micro-Animations** | EMV Chip Reader, Note Counting Shutter Dispenser, Vault Deposit Intake |
| 🧾 **Receipts** | **Thermal ATM Receipts** | Perforated cut lines, metadata headers, barcode footer, transaction details |
| 🔒 **Security** | **PBKDF2 + HMAC Pepper** | 100,000 hash rounds + 16-byte cryptographic salt + server secret pepper |
| 🛡️ **Anti-Tamper** | **Timing-Safe Verification** | Constant-time digest comparison via `secrets.compare_digest` |
| 🚫 **Protection** | **Brute-Force Lockout** | Immediate account locking upon 3 consecutive failed PIN attempts |
| ⚡ **Concurrency** | **ACID Guarantees** | `BEGIN IMMEDIATE TRANSACTION;` preventing write-lock collisions & race conditions |
| 💵 **Dispenser** | **Bounded Note Allocator** | Exact-change backtracking solver across physical note cassettes (`$500`, `$200`, `$100`) |
| 📜 **Auditability** | **Relational Ledger** | Full audit trail (`AUTHENTICATE`, `BALANCE_INQUIRY`, `WITHDRAWAL`, `DEPOSIT`, `LOCKOUT`) |
| 👔 **Admin Portal** | **Manager Dashboard** | Open/delete accounts, unlock accounts, search directory, live hash inspector |

---

## 🏛️ System Architecture

```text
┌────────────────────────────────────────────────────────┐
│                   Presentation Layer                   │
│        Customer ATM Terminal       Admin Portal        │
│             (main.py)               (admin.py)         │
└───────────┬───────────────────────────────┬────────────┘
            │                               │
            ▼                               ▼
┌────────────────────────────────────────────────────────┐
│              TrueColor TUI Engine (core/ui/)           │
│    • Components (Tables, Receipts, Masked PIN Input)   │
│    • Effects (Card Reading, Note Dispensing Counters)  │
│    • Theme (RGB TrueColor, Gradients, Glowing Badges)  │
└───────────┬───────────────────────────────┬────────────┘
            │                               │
            ▼                               ▼
┌────────────────────────────────────────────────────────┐
│             Service Layer (core/services/)             │
│  • BankingTransactionService   • AuthenticationService │
│  • VaultManagerService         • SecurityHashProvider  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│          Repository Interfaces (core/interfaces/)      │
│   IAccountRepository   ITransactionRepo   IVaultRepo   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│            Data Access Layer (core/repositories/)      │
│  • SqliteAccountRepository    • SqliteTransactionRepo  │
│  • SqliteVaultRepository      • Domain Model Converters│
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│           SQLite3 ACID Relational Database             │
│        (PRAGMA foreign_keys = ON, timeout = 5000)      │
└────────────────────────────────────────────────────────┘
```

---

## 🔒 Security & Cryptographic Model

1. **Version 3 Cryptographic Formulations**:
   - `peppered_key = HMAC-SHA256(key=SECRET_PEPPER, message=PIN)`
   - `pin_hash = "v3$" + PBKDF2-HMAC-SHA256(password=peppered_key, salt=salt, iterations=100000)`
2. **Unique Cryptographic Salt**: Each account generates a 16-byte cryptographically secure random salt (`secrets.token_hex(16)`), defeating rainbow table attacks.
3. **Server-Side Secret Pepper**: The pepper key resides strictly in application memory / configuration, ensuring hashes cannot be reversed even if the database is extracted.
4. **Timing-Safe Constant-Time Comparison**: PIN comparisons utilize `secrets.compare_digest()` to eliminate side-channel timing attack vectors.
5. **Brute-Force Lockout Defense**: Tracks consecutive failed authentication attempts. Upon the 3rd consecutive failed PIN:
   - Account is locked (`is_locked = 1`).
   - A `LOCKOUT` audit transaction is committed.
   - All subsequent authentication attempts are rejected until administratively unlocked.

---

## 💵 Cash Dispenser Algorithm

Standard ATM implementations often rely on simple Greedy algorithms that fail when specific note denominations are depleted. 

The **Advanced ATM Simulator** implements a recursive **Bounded Backtracking Algorithm** (`solve_denomination_allocation`):
- Explores note allocations across physical cassettes (`$500`, `$200`, `$100`).
- If taking a higher denomination note prevents making exact change from remaining inventory, the algorithm backtracks and evaluates alternative combinations.
- Guarantees exact cash dispensing whenever physically possible given current cassette stock.

---

## 💾 Database Schema & ACID Transactions

The SQLite relational database maintains strict referential integrity and write locks:

- **`accounts`**: Stores account numbers, customer names, PIN hashes, salts, balances, and security lockout states.
- **`transactions`**: Immutable audit ledger recording transaction types (`AUTHENTICATE`, `BALANCE_INQUIRY`, `WITHDRAWAL`, `DEPOSIT`, `LOCKOUT`), amounts, timestamps, and execution statuses.
- **`cash_vault`**: Physical cassette inventory tracking denomination values and remaining note counts.
- **Concurrency Safety**: Enforces `BEGIN IMMEDIATE TRANSACTION;` write locks and PRAGMA busy timeouts (`5000ms`) to eliminate race conditions and double-spending across parallel operations.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **SQLite 3.35+**

### Installation & Setup

```bash
git clone https://github.com/tarangsuryawanshitarang-eng/ATM-Simulator.git
cd ATM-Simulator

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install test dependencies
pip install -r requirements.txt
```

### Database Initialization

```bash
# Seed 30 demo accounts and cash vault cassettes (idempotent):
python database/seeder.py

# Force reset to clean seed state:
python database/seeder.py --reset
```

---

### Running the Customer ATM Kiosk

```bash
python main.py
```
- Interactive self-service ATM terminal.
- Features: Card insertion, real-time masked PIN entry, balance inquiry, fast cash, custom withdrawals with live note counting animations, cash deposits, mini-statements, thermal paper receipts, and PIN changes.

---

### Running the Bank Manager Portal

```bash
python admin.py
```
- Dedicated administrative management dashboard.
- Features: View account directory, open new accounts, close/delete accounts, inspect physical vault cassette capacity gauges, restock currency cassettes, unlock locked accounts, inspect cryptographic hashes, and review system audit ledgers.

---

## 🧪 Testing Suite

Run the full automated test suite using `pytest`:

```bash
pytest -v
```

### Test Coverage (32 Automated Tests):
- **`tests/test_account_creation.py`**: Account registration, duplicate prevention, and restart persistence.
- **`tests/test_domain_services.py`**: Domain entities (`Account`, `VaultCassette`), repository interfaces, and clean service layers.
- **`tests/test_security.py`**: PBKDF2 hashing, random salt generation, secret pepper defense, lockout triggers, and unlocking.
- **`tests/test_vault.py`**: Bounded backtracking note allocation, currency exhaustion handling, and inventory transitions.
- **`tests/test_concurrency.py`**: Multi-threaded ACID write locking, race condition prevention, and parallel withdrawal safety.

---

## 📁 Project Directory Structure

```text
ATM-Simulator/
├── .gitignore                      # Git ignore rules
├── README.md                       # System overview & documentation
├── requirements.txt                # Test dependencies (pytest)
├── main.py                         # Customer ATM terminal interface (TUI)
├── admin.py                        # Bank Manager dashboard + Hash Inspector (TUI)
├── config.py                       # Centralized configuration & constants
├── database/
│   ├── connection.py               # Thread-safe SQLite connection & PRAGMAs
│   ├── schema.sql                  # Relational DDL with strict integrity constraints
│   └── seeder.py                   # Seeds 30 demo accounts & cash vault
├── core/
│   ├── ui/                         # 24-bit TrueColor TUI Engine
│   │   ├── theme.py                # Gradients, ANSI TrueColor, badges & boxes
│   │   ├── effects.py              # Micro-animations (card reader, dispenser, vault)
│   │   └── components.py           # Masked PIN input, thermal receipts, tables & cards
│   ├── domain/                     # Pure Domain Models & Business Invariants
│   │   ├── account.py              # Account entity
│   │   ├── transaction.py          # TransactionRecord entity
│   │   └── vault.py                # VaultCassette entity
│   ├── interfaces/                 # Pure Abstract Base Classes (DIP & ISP)
│   │   ├── repositories.py         # IAccountRepository, ITransactionRepository, IVaultRepository
│   │   ├── security.py             # IHashProvider, IAuthenticationService
│   │   └── transaction.py          # ITransactionService, IVaultManagerService
│   ├── repositories/               # SQLite Data Access Layer
│   │   ├── account_repo.py         # SqliteAccountRepository
│   │   ├── transaction_repo.py     # SqliteTransactionRepository
│   │   └── vault_repo.py           # SqliteVaultRepository
│   ├── services/                   # Business Logic & Cryptography Services
│   │   ├── security.py             # Pbkdf2PepperHashProvider
│   │   ├── authentication.py       # AuthenticationService
│   │   ├── vault.py                # VaultManagerService
│   │   └── transaction.py          # BankingTransactionService
│   ├── exceptions.py               # Custom domain exception hierarchy
│   ├── security.py                 # Security facade
│   ├── vault.py                    # Vault facade
│   └── transaction.py              # Transaction facade
└── tests/
    ├── test_account_creation.py    # Account creation & persistence tests
    ├── test_domain_services.py     # Clean architecture domain & service tests
    ├── test_security.py            # PBKDF2 cryptography & lockout tests
    ├── test_vault.py               # Note allocation algorithm tests
    └── test_concurrency.py         # Multi-threaded ACID concurrency tests
```
