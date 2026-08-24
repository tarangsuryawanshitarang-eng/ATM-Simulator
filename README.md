# 🏧 Advanced ATM Simulator

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/Database-SQLite3-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite3"/>
  <img src="https://img.shields.io/badge/Transactions-ACID_Safe-success?style=for-the-badge" alt="ACID Safe"/>
  <img src="https://img.shields.io/badge/Security-PBKDF2--SHA256--Pepper-red?style=for-the-badge" alt="PBKDF2-SHA256-Pepper"/>
  <img src="https://img.shields.io/badge/UI-24--bit_TrueColor_TUI-cyan?style=for-the-badge" alt="TrueColor TUI"/>
  <img src="https://img.shields.io/badge/Architecture-SOLID_Clean_Design-purple?style=for-the-badge" alt="SOLID Clean Design"/>
  <img src="https://img.shields.io/badge/Tests-30%20Passing%20(100%25)-brightgreen?style=for-the-badge" alt="Tests"/>
</p>

<p align="center">
  <strong>An institutional-grade, transaction-safe Automated Teller Machine (ATM) simulation system engineered in Python and SQLite.</strong><br>
  Featuring a cutting-edge 24-bit TrueColor Terminal User Interface (TUI), clean Object-Oriented SOLID architecture, 100 Indian customer accounts, real-time masked PIN entry, live cash dispensing animations, authentic thermal paper receipts, and banking-grade PBKDF2 cryptography with HMAC Pepper defense.
</p>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features & Visual Highlights](#-key-features--visual-highlights)
- [System Architecture (HLD & LLD)](#-system-architecture-hld--lld)
- [Visual Design System & TUI Components](#-visual-design-system--tui-components)
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

The **Advanced ATM Simulator** models real-world automated banking kiosks with institutional-grade engineering rigor and visually stunning terminal aesthetics. It features:

1. **24-bit TrueColor Terminal Interface**: High-resolution RGB gradients, cardholder dashboard widgets, status badges, and interactive thermal receipts.
2. **Interactive Micro-Animations**: EMV chip reading simulations, motorized cash dispensing note counting, and optical vault deposit intake animations.
3. **Real-Time Masked PIN Input**: Real-time bullet masking (`●●●●`) with backspace support across Windows and POSIX terminals.
4. **Deterministic Multi-Denomination Dispenser**: Solves exact physical currency note combinations (`$500`, `$200`, `$100`) using bounded backtracking.
5. **True ACID Transaction Safety**: Enforces `BEGIN IMMEDIATE TRANSACTION;` write locks and SQLite PRAGMA busy timeouts to guarantee zero balance inconsistencies during simultaneous multi-threaded operations.
6. **Cryptographic Protection**: Secures user PINs via **PBKDF2-HMAC-SHA256** (100,000 iterations), unique 16-byte random salts, server-side HMAC secret pepper defense, timing-safe constant-time comparisons, and automatic 3-strike brute-force lockouts.
7. **Clean OOP & Layered Architecture**: Clear separation across Domain Entities (`Account`, `VaultCassette`), Abstract Interfaces (`IAccountRepository`, `IAuthenticationService`), Data Access Repositories (`SqliteAccountRepository`), and Domain Services (`BankingTransactionService`, `VaultManagerService`).
8. **100 Authentic Indian Accounts**: Seeded with diverse Indian customer profiles across accounts `10001` to `10100`.

---

## ✨ Key Features & Visual Highlights

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

## 🏛️ System Architecture (HLD & LLD)

```
                              ┌────────────────────────────────────────────────────────┐
                              │                   Presentation Layer                   │
                              │   • Customer ATM Kiosk TUI (main.py)                   │
                              │   • Bank Manager Executive Dashboard (admin.py)        │
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

---

## 🎨 Visual Design System & TUI Components (`core/ui/`)

- **`core/ui/theme.py`**:
  - `Gradient.cyan_to_emerald()`, `Gradient.gold_to_orange()`
  - `Badge.active()`, `Badge.locked()`, `Badge.success()`, `Badge.failed()`
- **`core/ui/effects.py`**:
  - `animate_card_reading()`: Visual chip reading simulation.
  - `animate_cash_dispensing()`: Multi-denomination note dispatch counting.
  - `animate_vault_deposit()`: Note verification and optical scan intake.
- **`core/ui/components.py`**:
  - `prompt_masked_pin()`: Interactive real-time bullet masking (`●●●●`).
  - `ThermalReceipt.render()`: Authentic paper receipts with barcode lines.
  - `TableFormatter.render_table()`: Formatted tables with gradient titles and column alignment.
  - `CardWidget.render_dashboard_card()`: Modern customer dashboard card widget.

---

## 👥 Demo Accounts & Test Credentials (100 Indian Accounts)

| Account Number | Account Holder | PIN | Starting Balance | Initial Status |
|:---|:---|:---:|:---:|:---:|
| **`10001`** | Tarang Suryawanshi (Lead Dev) | `1234` | `$2,500.00` | Active |
| **`10002`** | Sameep Patel (Project Partner) | `4321` | `$1,000.00` | Active |
| **`10003`** | Diya Iyer | `9999` | `$50.00` | Active |
| **`10004`** | Aditya Verma | `0000` | `$300.00` | **Locked** (Demo lockout) |
| **`10005`** | Aarav Sharma | `1111` | `$5,000.00` | Active |
| **`10006`** | Vivaan Patel | `2222` | `$7,500.00` | Active |
| **`10007`** | Ananya Gupta | `3333` | `$12,000.00` | Active |
| **`10008`** | Rahul Deshmukh | `4444` | `$3,200.00` | Active |
| **`10009`** | Sneha Joshi | `5555` | `$1,500.00` | Active |
| **`10010`** | Priya Nair | `6666` | `$8,900.00` | Active |
| *... (10011 - 10100)* | *(90 more accounts)* | *varies* | *varies* | Active |

> 📖 **Full Accounts & PIN Directory**: See [`TEST_CREDENTIALS.md`](file:///f:/Projects/Collage%20Project/ATM-Simulator/TEST_CREDENTIALS.md) for the complete list of all 100 Indian demo accounts, security PINs, starting balances, and presentation demo shortcuts.

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
- Insert your Card (e.g., `10001`) and PIN (`1234` with real-time `●●●●` masking).
- Check your balance, make fast-cash or custom withdrawals with live note counting animations, deposit cash, view your mini-statement, print receipts, or change your PIN.

---

### Running the Bank Manager Portal

```bash
python admin.py
```
- **Option 1**: Search & view all 100 customer accounts and aggregated balances.
- **Option 2**: Register a new customer bank account (auto-incrementing account numbering).
- **Option 3**: Close / Delete a customer account (with verification safeguard).
- **Option 4 & 5**: Inspect physical vault cassette capacity gauge bars (`[████████░░] 80%`) and replenish banknotes.
- **Option 6**: Unlock locked accounts (e.g. `10004`).
- **Option 7**: Run the **Live Cryptographic Hash & Security Inspector** (Academic Demo).
- **Option 8**: Filter and view system-wide transaction audit ledgers.
- **Option 9**: Factory reset database (protected with `CONFIRM RESET` verification).
- **Option 10**: Exit Admin Portal.

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
├── CHANGES.md                      # Comprehensive 5-branch project changelog
├── analysis_of_atm_simulation.md   # SOLID & HLD/LLD system design report
├── requirements.txt                # Test dependencies (pytest)
├── main.py                         # Customer ATM terminal interface (TUI)
├── admin.py                        # Bank Manager dashboard + Hash Inspector (TUI)
├── config.py                       # Centralized configuration & constants
├── database/
│   ├── connection.py               # Thread-safe SQLite connection & PRAGMAs
│   ├── schema.sql                  # Relational DDL with strict integrity constraints
│   └── seeder.py                   # Seeds 100 Indian customer accounts & vault
├── core/
│   ├── ui/                         # Next-Gen 24-bit TrueColor TUI Engine
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

This repository is organized across 5 evolutionary branches:
1. **`main`**: Initial baseline ATM simulator with SQLite backend and cassette management.
2. **`feature/admin-panel`**: Separation of Customer Kiosk (`main.py`) and Bank Manager Portal (`admin.py`), account unlocking, centralized account creation.
3. **`feature/security-v3-pepper`**: Cryptographic hardening with Version 3 Salt + HMAC Pepper defense and auto-upgrade.
4. **`feature/system-design-adaptation`**: Institutional SOLID & Clean Architecture refactoring, Domain-Driven Design, 100 Indian customer profiles, and Bank Manager account deletion.
5. **`feature/ui-enhancement`**: Next-Generation 24-bit TrueColor Terminal User Interface (TUI), real-time bullet PIN masking, animated cash dispensing, and authentic thermal paper receipts.

For full commit logs and detailed feature timelines, see [`CHANGES.md`](file:///f:/Projects/Collage%20Project/ATM-Simulator/CHANGES.md).
