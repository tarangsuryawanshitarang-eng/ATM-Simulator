# 📋 Comprehensive Project Changelog & Branch Evolution
## Advanced Automated Teller Machine (ATM) Simulation System

---

## 📌 Architectural Branch Chronology

```
[Initial Release] ──► [feature/admin-panel] ──► [feature/security-v3-pepper] ──► [feature/system-design-adaptation]
  (Baseline Core)       (Kiosk vs Admin Portal)     (Cryptographic Pepper v3)       (SOLID / OOP / DDD Clean Arch)
```

---

## 🏛️ Branch 1: Initial Core Release (`main`)
*Baseline multi-denomination ATM simulation with SQLite storage and ACID write locking.*

- **Deterministic Multi-Denomination Dispenser**:
  - Implemented exact-change bounded backtracking note allocator across physical cassettes (`$500`, `$200`, `$100`).
- **ACID Transaction Safety**:
  - Configured `sqlite3` in autocommit mode (`isolation_level=None`) with explicit `BEGIN IMMEDIATE TRANSACTION;` write locks and PRAGMA busy timeouts (`5000ms`) to eliminate race conditions and double-spending.
- **Cryptographic Foundations**:
  - PIN protection using PBKDF2-HMAC-SHA256 (100,000 iterations) with 16-byte random salts.
  - Brute-force lockout enforcement after 3 consecutive failed PIN attempts.
- **Relational Schema**:
  - Created tables for `accounts`, `transactions`, and `cash_vault`.
- **Idempotent Database Seeder**:
  - Seeded demo test accounts (`10001`, `10002`, `10003`, `10004`) and vault cassettes.

---

## 👔 Branch 2: Administrative Separation (`feature/admin-panel`)
*Separated customer kiosk experience from administrative bank management.*

- **Dedicated Bank Manager Portal (`admin.py`)**:
  - Engineered an isolated administrative console for authorized personnel.
  - Features include:
    - View all customer accounts and aggregated balances with strict privacy compliance (PINs and salts redacted).
    - Inspect physical vault cassette quantities and total cash held in the ATM.
    - Cassette replenishment and custom denomination note restocking.
    - Unlock locked customer accounts and reset failed attempt counters.
    - Filterable system-wide transaction and security audit logs (`WITHDRAWAL`, `DEPOSIT`, `LOCKOUT`, `AUTHENTICATE`).
    - Protected factory database reset with 2-step typed confirmation (`CONFIRM RESET`).
- **Centralized Customer Registration**:
  - Implemented administrative account creation with auto-generated sequential account numbers (`highest + 1`), $0.00 opening balance, and optional immediate cash deposit.
- **Customer ATM Kiosk Hardening (`main.py`)**:
  - Dedicated exclusively to active cardholders (Insert Card & PIN, Balance Inquiry, Fast Cash / Custom Withdrawal, Deposit, Mini-Statement, PIN Change, Card Eject).
- **Data Persistence Fix**:
  - Resolved non-reset seeder bug by introducing `ON CONFLICT DO NOTHING` during normal execution to preserve live customer balance changes, withdrawals, deposits, and unlock events.

---

## 🛡️ Branch 3: Cryptographic Pepper Hardening (`feature/security-v3-pepper`)
*Hardened security model against offline database leaks and dictionary attacks.*

- **Version 3 Cryptographic Standard (`v3$`)**:
  - Introduced server-side secret Pepper defense (`ATM_SECURITY_PEPPER` / `config.SECURITY_PEPPER_V3`).
  - Key derivation formula:
    $$\text{Key} = \text{PBKDF2-HMAC-SHA256}(\text{HMAC}_{\text{Pepper}}(\text{PIN}), \text{Salt}, \text{Iterations}=100,000)$$
  - Prevents offline dictionary attacks even if the database file is compromised.
- **Seamless Auto-Upgrade**:
  - Verified and automatically upgraded legacy unpeppered hashes to Version 3 (`v3$`) upon successful user login.
- **Constant-Time Verification**:
  - Enforced `secrets.compare_digest` across all PIN verifications to eliminate side-channel timing attacks.

---

## 🏗️ Branch 4: System Design & SOLID Adaptation (`feature/system-design-adaptation`)
*Refactored procedural modules into institutional Object-Oriented Clean Architecture (HLD/LLD).*

- **Comprehensive System Design Report (`analysis_of_atm_simulation.md`)**:
  - Complete architectural assessment covering SOLID principles, High-Level Design (HLD), Low-Level Design (LLD), and threat modeling.
- **Domain Layer (`core/domain/`)**:
  - `Account`: Rich domain entity encapsulating balance limits, withdrawal checks, deposits, and lockout state transitions.
  - `TransactionRecord`: Immutable value object for audit ledger tracking.
  - `VaultCassette`: Domain entity for cassette note arithmetic and denomination validation.
- **Interface Layer (`core/interfaces/`)**:
  - Defined pure Abstract Base Classes (ABCs):
    - `IAccountRepository`, `ITransactionRepository`, `IVaultRepository` (DIP & ISP).
    - `IHashProvider`, `IAuthenticationService`, `ITransactionService`, `IVaultManagerService`.
- **Repository Layer (`core/repositories/`)**:
  - `SqliteAccountRepository`, `SqliteTransactionRepository`, `SqliteVaultRepository` mapping SQL records to domain models.
- **Domain Services Layer (`core/services/`)**:
  - `Pbkdf2PepperHashProvider`: Strategy pattern implementation for PBKDF2 + Pepper cryptography.
  - `AuthenticationService`: Business domain service for login, lockout, and registration.
  - `VaultManagerService`: Encapsulated greedy backtracking cash dispenser.
  - `BankingTransactionService`: Coordinated balance inquiries, withdrawals, deposits, and statements.
- **Backward-Compatible Facades (`core/security.py`, `core/vault.py`, `core/transaction.py`)**:
  - Maintained 100% backward compatibility for all legacy entry points and test scripts.
- **Live Cryptographic Hash & Security Inspector (`admin.py`)**:
  - Added academic interactive demonstration tool for professors to inspect live salt generation, server pepper HMAC pre-hashing, 100,000 PBKDF2 iterations, and constant-time verification tests.
- **Test Suite Expansion (`tests/test_domain_services.py`)**:
  - Added 5 new unit tests verifying domain entity encapsulation, services, and repositories (27 passing tests in total).
