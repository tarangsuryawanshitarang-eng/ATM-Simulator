# 🏧 Advanced ATM Simulator

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/Database-SQLite3-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite3"/>
  <img src="https://img.shields.io/badge/Transactions-ACID_Safe-success?style=for-the-badge" alt="ACID Safe"/>
  <img src="https://img.shields.io/badge/Security-PBKDF2--SHA256--Pepper-red?style=for-the-badge" alt="PBKDF2-SHA256-Pepper"/>
  <img src="https://img.shields.io/badge/Architecture-SOLID_Clean_Design-purple?style=for-the-badge" alt="SOLID Clean Design"/>
  <img src="https://img.shields.io/badge/Tests-30%20Passing%20(100%25)-brightgreen?style=for-the-badge" alt="Tests"/>
</p>

<p align="center">
  <strong>An institutional-grade, transaction-safe Automated Teller Machine (ATM) simulation system engineered in Python and SQLite.</strong><br>
  Built with clean Object-Oriented SOLID architecture, Domain-Driven Design (DDD), 100 Indian customer demo accounts, banking-grade PBKDF2 cryptography with HMAC Pepper defense, exact-change cassette allocation algorithms, thread-safe ACID concurrency, and separate Customer Kiosk and Bank Manager interfaces.
</p>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture (HLD & LLD)](#-system-architecture-hld--lld)
- [SOLID Principles Implementation](#-solid-principles-implementation)
- [Security & Authentication Model](#-security--authentication-model)
- [Cassette & Denomination Allocation Algorithm](#-cassette--denomination-allocation-algorithm)
- [Database Schema](#-database-schema)
- [Demo Accounts & Test Credentials](#-demo-accounts--test-credentials)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation & Virtual Environment](#installation--virtual-environment)
  - [Database Initialization (100 Accounts)](#database-initialization-100-accounts)
  - [Running the Customer ATM Kiosk](#running-the-customer-atm-kiosk)
  - [Running the Bank Manager Portal](#running-the-bank-manager-portal)
  - [Live Cryptographic Hash Inspector](#live-cryptographic-hash-inspector)
- [Testing & Concurrency Verification](#-testing--concurrency-verification)
- [Project Directory Tree](#-project-directory-tree)
- [Branch Evolution & Changelog](#-branch-evolution--changelog)

---

## 🌟 Overview

The **Advanced ATM Simulator** models real-world automated banking kiosks with institutional-grade engineering rigor. It adheres to **SOLID design principles** and clean **Layered Architecture**, featuring:

1. **Deterministic Multi-Denomination Dispenser**: Solves exact physical currency note combinations (`$500`, `$200`, `$100`) using bounded backtracking.
2. **True ACID Transaction Safety**: Enforces `BEGIN IMMEDIATE TRANSACTION;` write locks and SQLite PRAGMA busy timeouts to guarantee zero balance inconsistencies during simultaneous multi-threaded operations.
3. **Cryptographic Protection**: Secures user PINs via **PBKDF2-HMAC-SHA256** (100,000 iterations), unique 16-byte random salts, server-side HMAC secret pepper defense, timing-safe constant-time comparisons, and automatic 3-strike brute-force lockouts.
4. **Clean OOP & Layered Architecture**: Clear separation across Domain Entities (`Account`, `VaultCassette`), Abstract Interfaces (`IAccountRepository`, `IAuthenticationService`), Data Access Repositories (`SqliteAccountRepository`), and Domain Services (`BankingTransactionService`, `VaultManagerService`).
5. **Separation of Concerns**: Strictly separates the Customer ATM Kiosk (`main.py`) from the Bank Manager Dashboard (`admin.py`).
6. **100 Authentic Indian Accounts**: Seeded with diverse Indian customer profiles across accounts `10001` to `10100`.

---

## ✨ Key Features

| Category | Capability | Technical Implementation |
|:---|:---|:---|
| 🏗️ **Architecture** | **SOLID & Clean Design** | Domain Entities, Repository Pattern, Dependency Inversion via ABCs |
| 🔒 **Security** | **PBKDF2 + HMAC Pepper** | 100,000 hash rounds + 16-byte cryptographic salt + server secret pepper |
| 🛡️ **Anti-Tamper** | **Timing-Safe Verification** | Constant-time digest comparison via `secrets.compare_digest` |
| 🚫 **Protection** | **Brute-Force Lockout** | Immediate account locking upon 3 consecutive failed PIN attempts |
| ⚡ **Concurrency** | **ACID Guarantees** | `BEGIN IMMEDIATE TRANSACTION;` preventing write-lock collisions & race conditions |
| 💵 **Dispenser** | **Bounded Note Allocator** | Exact-change backtracking solver across physical note cassettes (`$500`, `$200`, `$100`) |
| 📜 **Auditability** | **Relational Ledger** | Full audit trail (`AUTHENTICATE`, `BALANCE_INQUIRY`, `WITHDRAWAL`, `DEPOSIT`, `LOCKOUT`) |
| 👔 **Admin Portal** | **Manager Dashboard** | Open/delete accounts, unlock accounts, inspect balances, cash audit logs, live hash inspector |

---

## 🏛️ System Architecture (HLD & LLD)

```
                              ┌────────────────────────────────────────────────────────┐
                              │                   Presentation Layer                   │
                              │   • Customer ATM Kiosk (main.py)                       │
                              │   • Bank Manager Portal & Hash Inspector (admin.py)    │
                              └───────────────────────────┬────────────────────────────┘
                                                          │
                                                          ▼
                              ┌────────────────────────────────────────────────────────┐
                              │                 Domain Services Layer                  │
                              │   • AuthenticationService (core.services.auth)         │
                              │   • BankingTransactionService (core.services.tx)       │
                              │   • VaultManagerService (core.services.vault)          │
                              │   • Pbkdf2PepperHashProvider (core.services.security)  │
                              └───────────────────────────┬────────────────────────────┘
                                                          │
                                  ┌───────────────────────┴────────────────────────┐
                                  ▼                                                ▼
┌──────────────────────────────────────────────────┐    ┌──────────────────────────────────────────────────┐
│              Domain Entities Layer               │    │             Repository Storage Layer             │
│   • Account (core.domain.account)                │    │   • SqliteAccountRepository (core.repositories)  │
│   • TransactionRecord (core.domain.transaction)  │    │   • SqliteTransactionRepository                  │
│   • VaultCassette (core.domain.vault)            │    │   • SqliteVaultRepository                        │
└──────────────────────────────────────────────────┘    └──────────────────────────┬───────────────────────┘
                                                                                   │
                                                                                   ▼
                                                        ┌──────────────────────────────────────────────────┐
                                                        │           SQLite3 Relational Database            │
                                                        │   • PRAGMA foreign_keys = ON                     │
                                                        │   • PRAGMA busy_timeout = 5000                   │
                                                        └──────────────────────────────────────────────────┘
```

For complete technical specifications, review [`analysis_of_atm_simulation.md`](file:///f:/Projects/Collage%20Project/ATM-Simulator/analysis_of_atm_simulation.md).

---

## 📐 SOLID Principles Implementation

- **S (Single Responsibility)**: Domain models hold entity invariants, repositories manage SQL persistence, services orchestrate business workflows, and CLI scripts manage user interactions.
- **O (Open/Closed)**: Cryptographic hashing and cash dispensing are encapsulated behind polymorphic interfaces (`IHashProvider`, `IVaultManagerService`), enabling new algorithms without modifying core business rules.
- **L (Liskov Substitution)**: Any repository conforming to `IAccountRepository` (SQLite, in-memory mock) can be substituted transparently with zero behavioral regressions.
- **I (Interface Segregation)**: Granular, specialized contracts (`IAccountRepository`, `ITransactionRepository`, `IVaultRepository`) prevent clients from depending on methods they do not use.
- **D (Dependency Inversion)**: High-level services and presentation controllers depend on abstractions (`core.interfaces`), decoupled from low-level database implementations.

---

## 👥 Demo Accounts & Test Credentials (100 Indian Accounts)

| Account Number | Account Holder | PIN | Starting Balance | Initial Status |
|:---|:---|:---:|:---:|:---:|
| **`10001`** | Aarav Sharma | `1234` | `$2,500.00` | Active |
| **`10002`** | Vivaan Patel | `4321` | `$1,000.00` | Active |
| **`10003`** | Diya Iyer | `9999` | `$50.00` | Active |
| **`10004`** | Aditya Verma | `0000` | `$300.00` | **Locked** (Demo lockout) |
| **`10005`** | Tarang Suryawanshi | `1111` | `$5,000.00` | Active |
| **`10006`** | Sameep Patel | `2222` | `$7,500.00` | Active |
| **`10007`** | Ananya Gupta | `3333` | `$12,000.00` | Active |
| **`10008`** | Rahul Deshmukh | `4444` | `$3,200.00` | Active |
| **`10009`** | Sneha Joshi | `5555` | `$1,500.00` | Active |
| **`10010`** | Priya Nair | `6666` | `$8,900.00` | Active |
| *... (10011 - 10100)* | *(90 more accounts)* | *varies* | *varies* | Active |

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **SQLite 3.35+**

### Installation & Virtual Environment

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

### Database Initialization (100 Accounts)

```bash
# Seed 100 Indian demo accounts and cash vault cassettes (idempotent):
python database/seeder.py

# Force reset to factory seed state:
python database/seeder.py --reset
```

---

### Running the Customer ATM Kiosk

```bash
python main.py
```
- Insert your Card (e.g., `10001`) and PIN (`1234`).
- Check your balance, make fast-cash or custom withdrawals, deposit money in multiples of $100, view your mini-statement, or change your PIN.

---

### Running the Bank Manager Portal

```bash
python admin.py
```
- **Option 1**: View all 100 customer accounts and aggregated balances (PINs and salts are strictly redacted).
- **Option 2**: Register / open a new customer bank account with auto-generated sequential account numbers (`10101`, `10102`, etc.) and $0.00 opening balance.
- **Option 3**: **Close / Delete a Customer Account** (with confirmation safeguard).
- **Option 4 & 5**: Inspect physical vault cassette inventory and replenish banknotes.
- **Option 6**: Unlock locked accounts (e.g. `10004`).
- **Option 7**: Run the **Live Cryptographic Hash & Security Inspector** (Academic Demo).
- **Option 8**: Filter and view system-wide transaction audit ledgers.
- **Option 9**: Factory reset database (protected with `CONFIRM RESET` verification).
- **Option 10**: Exit Admin Portal.

---

### Live Cryptographic Hash Inspector

To demonstrate modern password/PIN security in real time (for classroom or academic presentation):
1. Launch `python admin.py`.
2. Select **Option 7 (`Cryptographic Hash & PIN Security Inspector`)**.
3. Enter any sample PIN or password to observe live salt generation, server pepper HMAC mixing, 100,000 PBKDF2 rounds, and constant-time verification tests.

---

## 🧪 Testing & Concurrency Verification

Run the comprehensive unit test suite:

```bash
pytest -v
```

The test suite covers:
- **`test_account_creation.py`**: Account registration, account deletion, duplicate account prevention, and persistence across restarts.
- **`test_domain_services.py`**: Clean architecture domain entities (`Account`, `VaultCassette`), repositories, and services.
- **`test_security.py`**: Cryptographic PBKDF2 hashing, unique salts, pepper defense, brute-force lockout, and unlock.
- **`test_vault.py`**: Backtracking denomination solver, cash exhaustion, and cassette inventory transitions.
- **`test_concurrency.py`**: ACID write locks preventing race condition overdrafts and parallel withdrawal double-spending.

---

## 📁 Project Directory Tree

```text
atm-simulator/
├── .gitignore                      # Ignores .venv, cache, and db files
├── README.md                       # Architecture & technical documentation
├── CHANGES.md                      # Comprehensive 4-branch project changelog
├── analysis_of_atm_simulation.md   # SOLID & HLD/LLD system design report
├── requirements.txt                # Test dependencies (pytest)
├── main.py                         # Customer ATM terminal interface
├── admin.py                        # Bank Manager dashboard + Hash Inspector
├── config.py                       # Centralized configuration & constants
├── database/
│   ├── connection.py               # Thread-safe SQLite connection & PRAGMAs
│   ├── schema.sql                  # Relational DDL with strict integrity constraints
│   └── seeder.py                   # Seeds 100 Indian customer accounts & vault
├── core/
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
│   ├── security.py                 # Backward-compatible security facade
│   ├── vault.py                    # Backward-compatible vault facade
│   └── transaction.py              # Backward-compatible transaction facade
└── tests/
    ├── test_account_creation.py    # Unit tests for account registration, deletion & persistence
    ├── test_domain_services.py     # Unit tests for domain entities & clean services
    ├── test_security.py            # Unit tests for PBKDF2 cryptography & lockout
    ├── test_vault.py               # Unit tests for backtracking note allocator
    └── test_concurrency.py         # ACID concurrency & race condition test suite
```

---

## 🌿 Branch Evolution & Changelog

This repository is organized across 4 evolutionary branches:
1. **`main`**: Initial baseline ATM simulator with SQLite backend and cassette management.
2. **`feature/admin-panel`**: Separation of Customer Kiosk (`main.py`) and Bank Manager Portal (`admin.py`), account unlocking, centralized account creation.
3. **`feature/security-v3-pepper`**: Cryptographic hardening with Version 3 Salt + HMAC Pepper defense and auto-upgrade.
4. **`feature/system-design-adaptation`**: Institutional SOLID & Clean Architecture refactoring, Domain-Driven Design, 100 Indian customer profiles, and Bank Manager account deletion.

For full commit logs and detailed feature timelines, see [`CHANGES.md`](file:///f:/Projects/Collage%20Project/ATM-Simulator/CHANGES.md).
