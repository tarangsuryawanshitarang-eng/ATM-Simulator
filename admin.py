"""
Bank Manager & System Administration Portal for the ATM Simulator.
Allows authorized administrators to inspect customer balances, manage vault cassettes,
review audit logs, and unlock accounts without exposing customer PINs or cryptographic salts.
"""

import os
import sys
from typing import Dict, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from core.exceptions import (
    AccountAlreadyExistsException,
    AccountNotFoundException,
    AtmBaseException,
    InvalidAmountException,
)
from core.security import create_account, delete_account, unlock_account
from core.transaction import deposit
from core.vault import get_total_vault_cash, get_vault_inventory, replenish_vault
from database.connection import get_db_connection
from database.seeder import seed_data


# ANSI Terminal Colors for Highlights
class Style:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def print_admin_banner() -> None:
    """Displays the administrative banner."""
    print(Style.CYAN + Style.BOLD + r"""
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║                ATM SYSTEM ADMINISTRATION & MANAGER PORTAL             ║
  ║                   Bank Manager Operational Dashboard                  ║
  ╚═══════════════════════════════════════════════════════════════════════╝
    """ + Style.RESET)


def view_all_accounts() -> None:
    """
    Fetches and presents all customer accounts with their balances and statuses.
    STRICT SECURITY RULE: Customer PINs and cryptographic salts are NEVER queried or exposed.
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            SELECT account_number, account_holder, balance, is_locked, failed_attempts, created_at
            FROM accounts
            ORDER BY account_number ASC;
            """
        )
        accounts = cursor.fetchall()

        total_customer_funds = sum(acc["balance"] for acc in accounts)
        locked_count = sum(1 for acc in accounts if acc["is_locked"] == 1)

        print(f"\n  ╔════════════════════════════════════════════════════════════════════════════════════════════════════╗")
        print(f"  ║                             BANK CUSTOMER ACCOUNTS & BALANCES OVERVIEW                               ║")
        print(f"  ╠══════════╦════════════════════════╦════════════════╦════════════╦═════════════╦══════════════════════╣")
        print(f"  ║ Acc #    ║ Account Holder         ║ Balance ($)    ║ Status     ║ Failed PINs ║ Created Timestamp    ║")
        print(f"  ╠══════════╬════════════════════════╬════════════════╬════════════╬═════════════╬══════════════════════╣")

        for acc in accounts:
            status_col = Style.RED if acc["is_locked"] == 1 else Style.GREEN
            status_str = "LOCKED" if acc["is_locked"] == 1 else "ACTIVE"
            status_txt = f"{status_col}{status_str:<6}{Style.RESET}"
            bal_str = f"${acc['balance']:,.2f}"
            print(f"  ║ {acc['account_number']:<8} ║ {acc['account_holder']:<22} ║ {bal_str:<14} ║ {status_txt} ║ {acc['failed_attempts']:<11} ║ {acc['created_at']:<20} ║")

        print(f"  ╠══════════╩════════════════════════╩════════════════╩════════════╩═════════════╩══════════════════════╣")
        print(f"  ║ Total Accounts: {len(accounts):<4} | Active Funds: {Style.GREEN}${total_customer_funds:,.2f}{Style.RESET} | Locked Accounts: {locked_count:<4}".ljust(111) + "║")
        print(f"  ╚════════════════════════════════════════════════════════════════════════════════════════════════════╝")
        print(Style.YELLOW + "  [!] Note: Customer PINs are securely hashed and redacted per privacy compliance." + Style.RESET)
    finally:
        conn.close()


def view_vault_cassettes() -> None:
    """Displays vault note quantities and monetary values in a clean table."""
    conn = get_db_connection()
    try:
        inventory = get_vault_inventory(conn)
        total_cash = get_total_vault_cash(conn)

        print(f"\n  ╔═══════════════════════════════════════════════════════════╗")
        print(f"  ║             PHYSICAL VAULT CASSETTE INVENTORY             ║")
        print(f"  ╠══════════════════╦════════════════════╦═══════════════════╣")
        print(f"  ║ Denomination     ║ Note Count         ║ Subtotal ($)      ║")
        print(f"  ╠══════════════════╬════════════════════╬═══════════════════╣")
        for denom in sorted(config.SUPPORTED_DENOMINATIONS, reverse=True):
            count = inventory.get(denom, 0)
            subtotal = denom * count
            print(f"  ║ ${denom:<15} ║ {count:<18} ║ ${subtotal:,.2f}".ljust(62) + "║")
        print(f"  ╠══════════════════╩════════════════════╩═══════════════════╣")
        print(f"  ║ Total Cash in ATM: {Style.GREEN}${total_cash:,.2f}{Style.RESET}".ljust(70) + "║")
        print(f"  ╚═══════════════════════════════════════════════════════════╝")
    finally:
        conn.close()


def refill_vault_cassettes() -> None:
    """Allows bank administrators to replenish notes in ATM cassettes."""
    print(Style.CYAN + "\n  [ REFILL VAULT NOTE CASSETTES ]" + Style.RESET)
    refills: Dict[int, int] = {}

    for denom in sorted(config.SUPPORTED_DENOMINATIONS, reverse=True):
        raw = input(f"  Enter new note count for ${denom} cassette (leave blank to keep current): ").strip()
        if raw:
            try:
                count = int(raw)
                if count < 0:
                    print(Style.RED + "  [-] Note count cannot be negative." + Style.RESET)
                    return
                refills[denom] = count
            except ValueError:
                print(Style.RED + "  [-] Invalid integer." + Style.RESET)
                return

    if refills:
        conn = get_db_connection()
        try:
            replenish_vault(conn, refills)
            print(Style.GREEN + "  [+] Vault cassettes replenished successfully!" + Style.RESET)
            view_vault_cassettes()
        finally:
            conn.close()
    else:
        print(Style.YELLOW + "  [*] No changes made to vault inventory." + Style.RESET)


def handle_create_account() -> None:
    """Allows an administrator to register/open a new customer bank account with auto-generated account number."""
    print(Style.CYAN + "\n  [ REGISTER NEW CUSTOMER ACCOUNT ]" + Style.RESET)

    # Automatically generate next account number (highest numeric account number + 1)
    conn = get_db_connection()
    new_acc_num = "10001"
    try:
        cursor = conn.execute(
            "SELECT account_number FROM accounts WHERE account_number GLOB '[0-9]*' ORDER BY CAST(account_number AS INTEGER) DESC LIMIT 1;"
        )
        row = cursor.fetchone()
        if row:
            try:
                new_acc_num = str(int(row["account_number"]) + 1)
            except ValueError:
                new_acc_num = "10001"
    finally:
        conn.close()

    print(f"  Auto-Generated Account Number : {Style.GREEN}{Style.BOLD}{new_acc_num}{Style.RESET}")

    holder = input("  Enter Customer Full Name      : ").strip()
    if not holder:
        print(Style.RED + "  [-] Customer name cannot be blank." + Style.RESET)
        return

    pin = input("  Set 4 or 6-Digit Security PIN : ").strip()
    if not (pin.isdigit() and len(pin) in (4, 6)):
        print(Style.RED + "  [-] PIN must be exactly 4 or 6 numeric digits." + Style.RESET)
        return

    pin_confirm = input("  Confirm Security PIN          : ").strip()
    if pin != pin_confirm:
        print(Style.RED + "  [-] Security PIN and confirmation do not match." + Style.RESET)
        return

    conn = get_db_connection()
    try:
        # Generate new account directly with $0.00 balance
        new_acc = create_account(conn, new_acc_num, holder, pin, 0.0)
        print(f"\n  ╔═══════════════════════════════════════════════════════════╗")
        print(f"  ║        {Style.GREEN}CUSTOMER ACCOUNT CREATED SUCCESSFULLY{Style.RESET}              ║")
        print(f"  ╠═══════════════════════════════════════════════════════════╣")
        print(f"  ║  Account Number : {new_acc['account_number']:<39} ║")
        print(f"  ║  Account Holder : {new_acc['account_holder']:<39} ║")
        print(f"  ║  Opening Balance: {Style.GREEN}${new_acc['balance']:,.2f}{Style.RESET}".ljust(70) + "║")
        print(f"  ║  Account Status : {Style.GREEN}ACTIVE{Style.RESET}".ljust(70) + "║")
        print(f"  ╚═══════════════════════════════════════════════════════════╝")

        # Inquire if customer wants to make an initial deposit
        print(f"\n  Initial Opening Balance is $0.00.")
        print(f"  [1] Make Cash Deposit (Multiples of $100)")
        print(f"  [2] Finish / Return to Main Manager Menu")
        dep_opt = input("  Select an option [1-2, Default: 2]: ").strip()

        if dep_opt == "1":
            raw_dep = input("  Enter deposit amount in multiples of $100: $").strip()
            if raw_dep:
                try:
                    dep_amount = float(raw_dep)
                    if dep_amount <= 0 or dep_amount % 100 != 0:
                        print(Style.RED + "  [-] Deposit amount must be a positive multiple of $100." + Style.RESET)
                    else:
                        dep_res = deposit(conn, new_acc_num, dep_amount)
                        print(Style.GREEN + f"\n  [+] Successfully deposited ${dep_amount:,.2f}. Updated balance: ${dep_res['new_balance']:,.2f}" + Style.RESET)
                except (InvalidAmountException, AtmBaseException) as e:
                    print(Style.RED + f"\n  [-] Deposit rejected: {e.message}" + Style.RESET)
                except ValueError:
                    print(Style.RED + "  [-] Invalid amount entered." + Style.RESET)
    except (AccountAlreadyExistsException, InvalidAmountException, AtmBaseException) as e:
        print(Style.RED + f"\n  [-] Account Creation Failed: {e.message}" + Style.RESET)
    except Exception as e:
        print(Style.RED + f"\n  [-] Unexpected error: {str(e)}" + Style.RESET)
    finally:
        conn.close()


def handle_delete_account() -> None:
    """Allows an administrator to close and delete a customer account."""
    print("\n  ┌───────────────────────────────────────────────────────────┐")
    print("  │               CLOSE / DELETE CUSTOMER ACCOUNT             │")
    print("  └───────────────────────────────────────────────────────────┘")

    acc_num = input("  Enter Account Number to DELETE (or press Enter to cancel): ").strip()
    if not acc_num:
        print(Style.YELLOW + "  [*] Account deletion cancelled." + Style.RESET)
        return

    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT account_number, account_holder, balance, is_locked FROM accounts WHERE account_number = ?;",
            (acc_num,),
        )
        row = cursor.fetchone()
        if row is None:
            print(Style.RED + f"\n  [-] Error: Account '{acc_num}' not found in database." + Style.RESET)
            return

        status_str = "LOCKED" if row["is_locked"] else "ACTIVE"
        print(f"\n  Account Details:")
        print(f"    • Account Number : {row['account_number']}")
        print(f"    • Account Holder : {row['account_holder']}")
        print(f"    • Current Balance: ${row['balance']:,.2f}")
        print(f"    • Status         : {status_str}")

        confirm = input(
            Style.RED
            + f"\n  Are you sure you want to permanently DELETE account '{acc_num}' ({row['account_holder']})? [y/N]: "
            + Style.RESET
        ).strip().lower()

        if confirm != "y":
            print(Style.YELLOW + "  [*] Account deletion aborted by administrator." + Style.RESET)
            return

        delete_account(conn, acc_num)
        print(
            Style.GREEN
            + f"\n  [+] SUCCESS: Customer account '{acc_num}' ({row['account_holder']}) has been permanently DELETED from the database."
            + Style.RESET
        )
    except AccountNotFoundException as e:
        print(Style.RED + f"\n  [-] Error: {e.message}" + Style.RESET)
    except Exception as e:
        print(Style.RED + f"\n  [-] Unexpected error during account deletion: {str(e)}" + Style.RESET)
    finally:
        conn.close()


def handle_unlock_account() -> None:
    """Allows an administrator to unlock a customer account."""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT account_number, account_holder FROM accounts WHERE is_locked = 1;")
        locked_rows = cursor.fetchall()
        if locked_rows:
            locked_list = ", ".join([f"{r['account_number']} ({r['account_holder']})" for r in locked_rows])
            print(Style.YELLOW + f"\n  [!] Currently locked accounts: {locked_list}" + Style.RESET)
        else:
            print(Style.GREEN + f"\n  [*] Notice: No accounts are currently flagged as locked." + Style.RESET)
    finally:
        conn.close()

    acc_num = input("  Enter Account Number to UNLOCK (or press Enter to cancel): ").strip()
    if not acc_num:
        print(Style.YELLOW + "  [*] Unlock operation cancelled." + Style.RESET)
        return

    conn = get_db_connection()
    try:
        # Check current status
        cursor = conn.execute(
            "SELECT account_holder, is_locked FROM accounts WHERE account_number = ?;",
            (acc_num,),
        )
        row = cursor.fetchone()
        if row is None:
            print(Style.RED + f"\n  [-] Error: Account '{acc_num}' not found in database." + Style.RESET)
            return

        if row["is_locked"] == 0:
            print(Style.YELLOW + f"\n  [*] Account '{acc_num}' ({row['account_holder']}) is already ACTIVE (not locked)." + Style.RESET)
            return

        unlock_account(conn, acc_num)
        print(Style.GREEN + f"\n  [+] SUCCESS: Account '{acc_num}' ({row['account_holder']}) has been UNLOCKED and failed PIN attempts reset to 0." + Style.RESET)
    except AccountNotFoundException as e:
        print(Style.RED + f"\n  [-] Error: {e.message}" + Style.RESET)
    except Exception as e:
        print(Style.RED + f"\n  [-] Unexpected error: {str(e)}" + Style.RESET)
    finally:
        conn.close()


def view_audit_logs() -> None:
    """
    Submenu for viewing global transaction audit trails.
    Stays inside the audit logs viewer until user explicitly returns to the main menu.
    """
    while True:
        print(f"\n  ┌───────────────────────────────────────────────────────────┐")
        print(f"  │              GLOBAL TRANSACTION AUDIT LEDGER              │")
        print(f"  ├───────────────────────────────────────────────────────────┤")
        print(f"  │  Filter by Category:                                      │")
        print(f"  │    [1] All Transactions                                   │")
        print(f"  │    [2] Cash Withdrawals Only                              │")
        print(f"  │    [3] Cash Deposits Only                                 │")
        print(f"  │    [4] Security Lockout Events                            │")
        print(f"  │    [5] Authentication Attempts                            │")
        print(f"  │    [6] Return to Main Manager Menu                        │")
        print(f"  └───────────────────────────────────────────────────────────┘")

        choice = input("  Select an audit filter [1-6]: ").strip()

        if choice == "6":
            break

        type_filter = None
        filter_label = "ALL RECENT TRANSACTIONS"
        if choice == "2":
            type_filter = "WITHDRAWAL"
            filter_label = "CASH WITHDRAWALS"
        elif choice == "3":
            type_filter = "DEPOSIT"
            filter_label = "CASH DEPOSITS"
        elif choice == "4":
            type_filter = "LOCKOUT"
            filter_label = "SECURITY LOCKOUT EVENTS"
        elif choice == "5":
            type_filter = "AUTHENTICATE"
            filter_label = "AUTHENTICATION ATTEMPTS"
        elif choice != "1":
            print(Style.RED + "  [-] Invalid filter selection. Please choose 1 to 6." + Style.RESET)
            continue

        conn = get_db_connection()
        try:
            if type_filter:
                cursor = conn.execute(
                    """
                    SELECT transaction_id, account_number, transaction_type, amount, status, failure_reason, timestamp
                    FROM transactions
                    WHERE transaction_type = ?
                    ORDER BY transaction_id DESC
                    LIMIT 25;
                    """,
                    (type_filter,),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT transaction_id, account_number, transaction_type, amount, status, failure_reason, timestamp
                    FROM transactions
                    ORDER BY transaction_id DESC
                    LIMIT 25;
                    """
                )
            rows = cursor.fetchall()

            print(f"\n  ╔════════════════════════════════════════════════════════════════════════════════════════════════════╗")
            print(f"  ║ {filter_label.center(98)} ║")
            print(f"  ╠═══════╦══════════╦══════════════════╦══════════════╦═══════════╦════════════════════╦════════════════════╣")
            print(f"  ║ Tx ID ║ Acc #    ║ Transaction Type ║ Amount ($)   ║ Status    ║ Failure / Note     ║ Timestamp          ║")
            print(f"  ╠═══════╬══════════╬══════════════════╬══════════════╬═══════════╬════════════════════╬════════════════════╣")

            if not rows:
                print(f"  ║                            No matching audit records found in ledger.                              ║")
            else:
                for r in rows:
                    amt_str = f"${r['amount']:,.2f}" if r["amount"] > 0 else "-"
                    status_col = Style.GREEN if r["status"] == "SUCCESS" else Style.RED
                    status_txt = f"{status_col}{r['status']:<8}{Style.RESET}"
                    reason_txt = (r["failure_reason"] or "-")[:18]
                    print(f"  ║ #{r['transaction_id']:<5} ║ {r['account_number']:<8} ║ {r['transaction_type']:<16} ║ {amt_str:<12} ║ {status_txt} ║ {reason_txt:<18} ║ {r['timestamp']:<18} ║")

            print(f"  ╚═══════╩══════════╩══════════════════╩══════════════╩═══════════╩════════════════════╩════════════════════╝")
        finally:
            conn.close()


def handle_crypto_hash_inspector() -> None:
    """
    Live Demonstration & Security Inspector for PBKDF2-HMAC-SHA256 with Pepper & Salt.
    Allows administrators and students to demonstrate modern cryptographic key derivation.
    """
    from core.services.security import Pbkdf2PepperHashProvider

    provider = Pbkdf2PepperHashProvider()

    print(Style.CYAN + Style.BOLD + r"""
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║       🔐 LIVE CRYPTOGRAPHIC HASH & SECURITY INSPECTOR (ACADEMIC)      ║
  ║         PBKDF2-HMAC-SHA256 (100,000 Rounds) + Per-User Salt + Pepper  ║
  ╚═══════════════════════════════════════════════════════════════════════╝
    """ + Style.RESET)

    test_input = input("  Enter any sample PIN / Password to inspect: ").strip()
    if not test_input:
        test_input = "1234"
        print(f"  [Default Sample PIN chosen: {test_input}]")

    # Generate salt and compute hash
    salt = provider.generate_salt()
    pepper_secret = provider.default_pepper
    v3_hash = provider.hash_pin(test_input, salt)

    print(f"\n  ╔════════════════════════════════════════════════════════════════════════════════════════════════════╗")
    print(f"  ║                                 CRYPTOGRAPHIC DERIVATION BREAKDOWN                                 ║")
    print(f"  ╠══════════════════════════════════╦═════════════════════════════════════════════════════════════════╣")
    print(f"  ║ Plaintext Input (Never Stored)   ║ {test_input:<63} ║")
    print(f"  ║ Cryptographic Random Salt        ║ {salt:<63} ║")
    print(f"  ║ Server-Side Pepper Secret (HMAC) ║ {pepper_secret[:40] + '...':<63} ║")
    print(f"  ║ PBKDF2 Iteration Work Factor     ║ 100,000 Rounds (HMAC-SHA256)                                    ║")
    print(f"  ║ Output Format Identifier         ║ Version 3 (Prefix: 'v3$')                                       ║")
    print(f"  ╠══════════════════════════════════╩═════════════════════════════════════════════════════════════════╣")
    print(f"  ║ Final One-Way Hash Stored in Database:                                                             ║")
    print(f"  ║   {Style.GREEN}{v3_hash}{Style.RESET}                               ║")
    print(f"  ╚════════════════════════════════════════════════════════════════════════════════════════════════════╝")

    print(Style.YELLOW + "\n  [!] Testing Constant-Time Verification against Attacks:" + Style.RESET)
    verify_test = input(f"  Enter PIN to test verification (try '{test_input}' or a wrong PIN): ").strip()
    is_match = provider.verify_pin(verify_test, salt, v3_hash)

    if is_match:
        print(Style.GREEN + f"  [+] Verification Result: TRUE (PIN Matches - Constant-time check passed)" + Style.RESET)
    else:
        print(Style.RED + f"  [-] Verification Result: FALSE (PIN Does Not Match - Access Denied)" + Style.RESET)

    input("\n  Press Enter to return to Manager Menu...")


def reset_database_safely() -> None:
    """
    Safely handles database reset with a conscious 2-step verification
    requiring the exact phrase 'CONFIRM RESET' to prevent accidental data loss.
    """
    print(Style.RED + "\n  ╔═══════════════════════════════════════════════════════════╗")
    print("  ║                   ⚠️  CRITICAL WARNING  ⚠️                  ║")
    print("  ╠═══════════════════════════════════════════════════════════╣")
    print("  ║ This operation will COMPLETELY WIPE all customer balances,║")
    print("  ║ PINs, and transaction audit ledgers, restoring the factory║")
    print("  ║ seed demo records. This action CANNOT be undone!          ║")
    print("  ╚═══════════════════════════════════════════════════════════╝" + Style.RESET)

    confirm_phrase = input("\n  To proceed, please type '" + Style.BOLD + "CONFIRM RESET" + Style.RESET + "' (or press Enter to cancel): ").strip()

    if confirm_phrase == "CONFIRM RESET":
        seed_data(reset=True)
        print(Style.GREEN + "\n  [+] Database has been successfully reset to default factory seed state." + Style.RESET)
    else:
        print(Style.YELLOW + "\n  [*] Confirmation phrase did not match. Database reset was ABORTED safely." + Style.RESET)


def admin_main() -> None:
    """Main execution loop for Bank Manager / Admin Portal."""
    if not config.DB_PATH.exists():
        seed_data(reset=False)

    print_admin_banner()

    while True:
        print(f"\n  ╔═══════════════════════════════════════════════════════╗")
        print(f"  ║               BANK MANAGER CONTROL PANEL              ║")
        print(f"  ╚═══════════════════════════════════════════════════════╝")
        print(f"  [1] View All Customer Accounts & Total Balances (SQL)")
        print(f"  [2] Open / Register New Customer Account")
        print(f"  [3] Close / Delete a Customer Account")
        print(f"  [4] Inspect Physical Vault Cassette Inventory")
        print(f"  [5] Refill / Set Vault Cassette Note Counts")
        print(f"  [6] Unlock a Locked Customer Account")
        print(f"  [7] Cryptographic Hash & PIN Security Inspector (Live Demo)")
        print(f"  [8] Inspect Global Transaction & Security Audit Logs")
        print(f"  [9] Reset Database to Factory Seed State (Protected)")
        print(f"  [10] Exit Admin Portal")
        print("  " + "-" * 55)

        choice = input("  Select an administrative action [1-10]: ").strip()

        if choice == "1":
            view_all_accounts()
        elif choice == "2":
            handle_create_account()
        elif choice == "3":
            handle_delete_account()
        elif choice == "4":
            view_vault_cassettes()
        elif choice == "5":
            refill_vault_cassettes()
        elif choice == "6":
            handle_unlock_account()
        elif choice == "7":
            handle_crypto_hash_inspector()
        elif choice == "8":
            view_audit_logs()
        elif choice == "9":
            reset_database_safely()
        elif choice == "10":
            print(Style.CYAN + "\n  [+] Exiting Admin Portal. Have a great day!\n" + Style.RESET)
            break
        else:
            print(Style.RED + "  [-] Invalid selection. Please enter a number between 1 and 10." + Style.RESET)



if __name__ == "__main__":
    try:
        admin_main()
    except KeyboardInterrupt:
        print("\n\n  [!] Admin session cancelled by user. Exiting safely.")
        sys.exit(0)


