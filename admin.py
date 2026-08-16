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
from core.exceptions import AccountNotFoundException, AtmBaseException
from core.security import unlock_account
from core.vault import get_total_vault_cash, get_vault_inventory, replenish_vault
from database.connection import get_db_connection
from database.seeder import seed_data


# ANSI Terminal Colors
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def print_admin_banner() -> None:
    """Displays the administrative banner."""
    print(Colors.BLUE + Colors.BOLD + r"""
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║                ATM SYSTEM ADMINISTRATION & MANAGER PORTAL             ║
  ║                   Bank Manager Operational Dashboard                  ║
  ╚═══════════════════════════════════════════════════════════════════════╝
    """ + Colors.RESET)


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

        print(Colors.CYAN + "\n  [ BANK CUSTOMER ACCOUNTS & BALANCES OVERVIEW ]" + Colors.RESET)
        print("  " + "=" * 90)
        print(f"  {'Acc #':<8} | {'Account Holder':<22} | {'Balance ($)':<14} | {'Status':<10} | {'Failed PINs':<11} | {'Created At'}")
        print("  " + "-" * 90)

        for acc in accounts:
            status_str = f"{Colors.RED}LOCKED{Colors.RESET}" if acc["is_locked"] == 1 else f"{Colors.GREEN}ACTIVE{Colors.RESET}"
            bal_str = f"${acc['balance']:,.2f}"
            print(f"  {acc['account_number']:<8} | {acc['account_holder']:<22} | {bal_str:<14} | {status_str:<19} | {acc['failed_attempts']:<11} | {acc['created_at']}")

        print("  " + "=" * 90)
        print(f"  Total Registered Accounts : {len(accounts)}")
        print(f"  Total Customer Deposits   : ${total_customer_funds:,.2f}")
        print(f"  Locked Accounts Count     : {locked_count}")
        print(Colors.YELLOW + "  [!] Note: Customer PINs are securely hashed and redacted per privacy compliance." + Colors.RESET)
    finally:
        conn.close()


def view_vault_cassettes() -> None:
    """Displays vault note quantities and monetary values."""
    conn = get_db_connection()
    try:
        inventory = get_vault_inventory(conn)
        total_cash = get_total_vault_cash(conn)

        print(Colors.BLUE + "\n  [ PHYSICAL VAULT CASSETTE INVENTORY ]" + Colors.RESET)
        print("  " + "=" * 55)
        print(f"  {'Denomination':<15} | {'Note Count':<12} | {'Subtotal ($)'}")
        print("  " + "-" * 55)
        for denom in sorted(config.SUPPORTED_DENOMINATIONS, reverse=True):
            count = inventory.get(denom, 0)
            subtotal = denom * count
            print(f"  ${denom:<14} | {count:<12} | ${subtotal:,.2f}")
        print("  " + "=" * 55)
        print(f"  Total Cash Available for Dispense: ${total_cash:,.2f}")
    finally:
        conn.close()


def refill_vault_cassettes() -> None:
    """Allows bank administrators to replenish notes in ATM cassettes."""
    print(Colors.CYAN + "\n  [ REFILL VAULT NOTE CASSETTES ]" + Colors.RESET)
    refills: Dict[int, int] = {}

    for denom in sorted(config.SUPPORTED_DENOMINATIONS, reverse=True):
        raw = input(f"  Enter new note count for ${denom} cassette (leave blank to keep current): ").strip()
        if raw:
            try:
                count = int(raw)
                if count < 0:
                    print(Colors.RED + "  [-] Note count cannot be negative." + Colors.RESET)
                    return
                refills[denom] = count
            except ValueError:
                print(Colors.RED + "  [-] Invalid integer." + Colors.RESET)
                return

    if refills:
        conn = get_db_connection()
        try:
            replenish_vault(conn, refills)
            print(Colors.GREEN + "  [+] Vault cassettes replenished successfully!" + Colors.RESET)
            view_vault_cassettes()
        finally:
            conn.close()
    else:
        print(Colors.YELLOW + "  [*] No changes made to vault inventory." + Colors.RESET)


def handle_unlock_account() -> None:
    """Allows an administrator to unlock a customer account."""
    acc_num = input("\n  Enter Account Number to UNLOCK: ").strip()
    if not acc_num:
        print(Colors.RED + "  [-] Account number cannot be blank." + Colors.RESET)
        return

    conn = get_db_connection()
    try:
        unlock_account(conn, acc_num)
        print(Colors.GREEN + f"  [+] Account '{acc_num}' has been successfully UNLOCKED and failed attempts reset." + Colors.RESET)
    except AccountNotFoundException as e:
        print(Colors.RED + f"  [-] Error: {e.message}" + Colors.RESET)
    except Exception as e:
        print(Colors.RED + f"  [-] Unexpected error: {str(e)}" + Colors.RESET)
    finally:
        conn.close()


def view_audit_logs() -> None:
    """Displays global transaction audit trail."""
    print("\n  [ GLOBAL TRANSACTION AUDIT TRAIL ]")
    print("  Filters: [1] All Events  [2] Withdrawals  [3] Deposits  [4] Lockouts  [5] Authentications")
    filter_choice = input("  Select filter [1-5, default 1]: ").strip() or "1"

    type_filter = None
    if filter_choice == "2":
        type_filter = "WITHDRAWAL"
    elif filter_choice == "3":
        type_filter = "DEPOSIT"
    elif filter_choice == "4":
        type_filter = "LOCKOUT"
    elif filter_choice == "5":
        type_filter = "AUTHENTICATE"

    conn = get_db_connection()
    try:
        if type_filter:
            cursor = conn.execute(
                """
                SELECT transaction_id, account_number, transaction_type, amount, status, failure_reason, timestamp
                FROM transactions
                WHERE transaction_type = ?
                ORDER BY transaction_id DESC
                LIMIT 30;
                """,
                (type_filter,),
            )
        else:
            cursor = conn.execute(
                """
                SELECT transaction_id, account_number, transaction_type, amount, status, failure_reason, timestamp
                FROM transactions
                ORDER BY transaction_id DESC
                LIMIT 30;
                """
            )
        rows = cursor.fetchall()

        print(Colors.CYAN + f"\n  [ DISPLAYING {len(rows)} RECENT AUDIT RECORDS ]" + Colors.RESET)
        print("  " + "=" * 90)
        print(f"  {'Tx ID':<7} | {'Acc #':<8} | {'Type':<16} | {'Amount ($)':<12} | {'Status':<9} | {'Reason':<18} | {'Timestamp'}")
        print("  " + "-" * 90)

        for r in rows:
            amt_str = f"${r['amount']:,.2f}" if r["amount"] > 0 else "-"
            status_color = Colors.GREEN if r["status"] == "SUCCESS" else Colors.RED
            status_str = f"{status_color}{r['status']:<9}{Colors.RESET}"
            reason_str = r["failure_reason"] or "-"
            print(f"  {r['transaction_id']:<7} | {r['account_number']:<8} | {r['transaction_type']:<16} | {amt_str:<12} | {status_str} | {reason_str:<18} | {r['timestamp']}")

        print("  " + "=" * 90)
    finally:
        conn.close()


def reset_database() -> None:
    """Restores database to pristine factory seed state."""
    confirm = input(Colors.RED + "  [!] WARNING: This will reset all accounts and transaction history. Confirm? [y/N]: " + Colors.RESET).strip().lower()
    if confirm == "y":
        seed_data(reset=True)
        print(Colors.GREEN + "  [+] Database reset and seeded with initial demo records." + Colors.RESET)
    else:
        print(Colors.YELLOW + "  [*] Database reset cancelled." + Colors.RESET)


def admin_main() -> None:
    """Main execution loop for Bank Manager / Admin Portal."""
    # Ensure database exists
    if not config.DB_PATH.exists():
        seed_data(reset=False)

    print_admin_banner()

    while True:
        print("\n  ╔═══════════════════════════════════════════════════════╗")
        print("  ║               BANK MANAGER CONTROL PANEL              ║")
        print("  ╚═══════════════════════════════════════════════════════╝")
        print("  [1] View All Customer Accounts & Total Balances (SQL)")
        print("  [2] Inspect Physical Vault Cassette Inventory")
        print("  [3] Refill / Set Vault Cassette Note Counts")
        print("  [4] Unlock a Locked Customer Account")
        print("  [5] Inspect Global Transaction & Security Audit Logs")
        print("  [6] Reset Database to Default Seed State")
        print("  [7] Exit Admin Portal")
        print("  " + "-" * 55)

        choice = input("  Select an administrative action [1-7]: ").strip()

        if choice == "1":
            view_all_accounts()
        elif choice == "2":
            view_vault_cassettes()
        elif choice == "3":
            refill_vault_cassettes()
        elif choice == "4":
            handle_unlock_account()
        elif choice == "5":
            view_audit_logs()
        elif choice == "6":
            reset_database()
        elif choice == "7":
            print(Colors.BLUE + "\n  [+] Exiting Admin Portal. Have a great day!\n" + Colors.RESET)
            break
        else:
            print(Colors.RED + "  [-] Invalid selection. Please enter a number between 1 and 7." + Colors.RESET)


if __name__ == "__main__":
    try:
        admin_main()
    except KeyboardInterrupt:
        print("\n\n  [!] Admin session cancelled by user. Exiting safely.")
        sys.exit(0)
