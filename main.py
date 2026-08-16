"""
Main Application Entry Point for the Advanced ATM Simulator.
Provides an interactive, menu-driven CLI terminal interface with input sanitization,
secure credential handling, physical cassette visibility, and session state management.
"""

import getpass
import os
import sys
from typing import Dict, Optional

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from core.exceptions import (
    AccountLockedException,
    AccountNotFoundException,
    AtmBaseException,
    AtmCashExhaustedException,
    AuthenticationFailedException,
    InsufficientFundsException,
    InvalidAmountException,
    UnsupportedDenominationException,
)
from core.security import authenticate_user
from core.transaction import (
    change_pin,
    deposit,
    get_account_details,
    get_balance,
    get_transaction_history,
    withdraw,
)
from core.vault import get_total_vault_cash, get_vault_inventory, replenish_vault
from database.connection import get_db_connection
from database.seeder import seed_data


# ANSI Color Codes for Terminal Styling
class TerminalColor:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"


def clear_screen() -> None:
    """Clears the console screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_banner() -> None:
    """Displays the ASCII header banner."""
    print(TerminalColor.CYAN + TerminalColor.BOLD + r"""
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║                 ADVANCED TRANSACTION-SAFE ATM SIMULATOR              ║
  ║                   SQLite3 ACID Backend & Vault Cassettes              ║
  ╚═══════════════════════════════════════════════════════════════════════╝
    """ + TerminalColor.RESET)


def print_demo_credentials() -> None:
    """Displays test accounts for convenience."""
    print(TerminalColor.YELLOW + "\n  [ DEMO ACCOUNTS & PIN CHEAT SHEET ]" + TerminalColor.RESET)
    print("  " + "-" * 55)
    print("  Account: 10001 | PIN: 1234 | Alice Smith   | Bal: $2,500.00")
    print("  Account: 10002 | PIN: 4321 | Bob Jones     | Bal: $1,000.00")
    print("  Account: 10003 | PIN: 9999 | Charlie Brown | Bal:    $50.00")
    print("  Account: 10004 | PIN: 0000 | Locked User   | [LOCKED]")
    print("  " + "-" * 55)


def show_vault_status() -> None:
    """Displays physical cassette note inventory."""
    conn = get_db_connection()
    try:
        inventory = get_vault_inventory(conn)
        total_cash = get_total_vault_cash(conn)
        print(TerminalColor.BLUE + "\n  [ PHYSICAL VAULT CASSETTE INVENTORY ]" + TerminalColor.RESET)
        print("  " + "=" * 45)
        for denom in sorted(config.SUPPORTED_DENOMINATIONS, reverse=True):
            count = inventory.get(denom, 0)
            subtotal = denom * count
            print(f"  Cassette ${denom:3d} : {count:4d} notes | Subtotal: ${subtotal:7,d}")
        print("  " + "-" * 45)
        print(f"  Total Vault Cash : ${total_cash:10,d}")
        print("  " + "=" * 45)
    finally:
        conn.close()


def prompt_pin(prompt_text: str = "Enter PIN: ") -> str:
    """Prompts for PIN reliably across all terminal environments without freezing."""
    pin = input(f"  {prompt_text}").strip()
    return pin



class AtmSession:
    """Manages active customer session state and transaction workflows."""

    def __init__(self, account_number: str, account_holder: str):
        self.account_number = account_number
        self.account_holder = account_holder

    def run_menu(self) -> None:
        """Customer main menu loop."""
        while True:
            print(TerminalColor.BOLD + f"\n  Logged in as: {self.account_holder} (Acc: {self.account_number})" + TerminalColor.RESET)
            print("  " + "=" * 45)
            print("  [1] Balance Inquiry")
            print("  [2] Cash Withdrawal (Standard / Fast Cash)")
            print("  [3] Cash Deposit (By Note Breakdown)")
            print("  [4] Mini-Statement (Recent Transactions)")
            print("  [5] Change PIN")
            print("  [6] Logout & Eject Card")
            print("  " + "=" * 45)

            choice = input("  Select an option [1-6]: ").strip()

            if choice == "1":
                self.handle_balance_inquiry()
            elif choice == "2":
                self.handle_withdrawal()
            elif choice == "3":
                self.handle_deposit()
            elif choice == "4":
                self.handle_statement()
            elif choice == "5":
                self.handle_change_pin()
            elif choice == "6":
                print(TerminalColor.GREEN + f"\n  [+] Session ended. Thank you for banking with us, {self.account_holder}!\n" + TerminalColor.RESET)
                break
            else:
                print(TerminalColor.RED + "  [-] Invalid selection. Please enter a number from 1 to 6." + TerminalColor.RESET)

    def handle_balance_inquiry(self) -> None:
        """Queries and presents account balance."""
        conn = get_db_connection()
        try:
            balance = get_balance(conn, self.account_number)
            print(TerminalColor.GREEN + f"\n  >>> Available Balance: ${balance:,.2f}" + TerminalColor.RESET)
        except AtmBaseException as e:
            print(TerminalColor.RED + f"\n  [-] Balance inquiry failed: {e.message}" + TerminalColor.RESET)
        finally:
            conn.close()

    def handle_withdrawal(self) -> None:
        """Handles fast cash and custom cash withdrawal."""
        print("\n  [ CASH WITHDRAWAL ]")
        print("  Fast Cash: [1] $100  [2] $200  [3] $500  [4] $1,000  [5] $2,000")
        print("  Custom:    [6] Enter other amount")
        print("  Cancel:    [7] Return to main menu")

        fast_cash_map = {"1": 100, "2": 200, "3": 500, "4": 1000, "5": 2000}
        sub_choice = input("  Select withdrawal option [1-7]: ").strip()

        if sub_choice in fast_cash_map:
            amount = float(fast_cash_map[sub_choice])
        elif sub_choice == "6":
            raw_amt = input("  Enter withdrawal amount (multiples of $100): $").strip()
            try:
                amount = float(raw_amt)
            except ValueError:
                print(TerminalColor.RED + "  [-] Invalid amount entered. Must be a numeric value." + TerminalColor.RESET)
                return
        elif sub_choice == "7":
            return
        else:
            print(TerminalColor.RED + "  [-] Invalid choice." + TerminalColor.RESET)
            return

        conn = get_db_connection()
        try:
            result = withdraw(conn, self.account_number, amount)
            print(TerminalColor.GREEN + "\n  ╔══════════════════════════════════════════════════════════════╗")
            print(f"  ║ WITHDRAWAL SUCCESSFUL: ${result['amount']:,.2f}".ljust(64) + "║")
            print("  ╠══════════════════════════════════════════════════════════════╣")
            print("  ║ Notes Dispensed:".ljust(64) + "║")
            for denom, count in sorted(result["dispensed_notes"].items(), reverse=True):
                print(f"  ║   • ${denom} x {count} note(s) = ${denom * count:,d}".ljust(64) + "║")
            print("  ╠══════════════════════════════════════════════════════════════╣")
            print(f"  ║ New Account Balance: ${result['new_balance']:,.2f}".ljust(64) + "║")
            print("  ╚══════════════════════════════════════════════════════════════╝" + TerminalColor.RESET)
        except (InsufficientFundsException, AtmCashExhaustedException, UnsupportedDenominationException, InvalidAmountException, AccountLockedException) as e:
            print(TerminalColor.RED + f"\n  [-] Withdrawal Rejected: {e.message}" + TerminalColor.RESET)
        except Exception as e:
            print(TerminalColor.RED + f"\n  [-] System error during withdrawal: {str(e)}" + TerminalColor.RESET)
        finally:
            conn.close()

    def handle_deposit(self) -> None:
        """Handles physical note cash deposit."""
        print("\n  [ CASH DEPOSIT - NOTE INSERTION ]")
        print("  Please insert physical notes ($500, $200, $100):")
        notes: Dict[int, int] = {}

        for denom in sorted(config.SUPPORTED_DENOMINATIONS, reverse=True):
            raw = input(f"  Number of ${denom} notes to insert (default 0): ").strip()
            if not raw:
                notes[denom] = 0
            else:
                try:
                    count = int(raw)
                    if count < 0:
                        print(TerminalColor.RED + "  [-] Count cannot be negative." + TerminalColor.RESET)
                        return
                    notes[denom] = count
                except ValueError:
                    print(TerminalColor.RED + "  [-] Invalid integer count." + TerminalColor.RESET)
                    return

        total_declared = sum(d * c for d, c in notes.items())
        if total_declared == 0:
            print(TerminalColor.YELLOW + "  [*] No notes inserted. Deposit cancelled." + TerminalColor.RESET)
            return

        print(f"  Total amount to deposit: ${total_declared:,.2f}")
        confirm = input("  Confirm deposit? [y/N]: ").strip().lower()
        if confirm != "y":
            print(TerminalColor.YELLOW + "  [*] Deposit cancelled." + TerminalColor.RESET)
            return

        conn = get_db_connection()
        try:
            result = deposit(conn, self.account_number, notes)
            print(TerminalColor.GREEN + "\n  ╔══════════════════════════════════════════════════════════════╗")
            print(f"  ║ DEPOSIT SUCCESSFUL: ${result['deposited_amount']:,.2f}".ljust(64) + "║")
            print("  ╠══════════════════════════════════════════════════════════════╣")
            print(f"  ║ New Account Balance: ${result['new_balance']:,.2f}".ljust(64) + "║")
            print("  ╚══════════════════════════════════════════════════════════════╝" + TerminalColor.RESET)
        except AtmBaseException as e:
            print(TerminalColor.RED + f"\n  [-] Deposit Failed: {e.message}" + TerminalColor.RESET)
        except Exception as e:
            print(TerminalColor.RED + f"\n  [-] System error during deposit: {str(e)}" + TerminalColor.RESET)
        finally:
            conn.close()

    def handle_statement(self) -> None:
        """Retrieves and displays recent transaction history."""
        conn = get_db_connection()
        try:
            history = get_transaction_history(conn, self.account_number, limit=10)
            print(TerminalColor.CYAN + f"\n  [ MINI-STATEMENT: LAST {len(history)} TRANSACTIONS ]" + TerminalColor.RESET)
            print("  " + "-" * 75)
            print(f"  {'ID':<5} | {'Type':<16} | {'Amount':<10} | {'Status':<9} | {'Timestamp':<19}")
            print("  " + "-" * 75)
            for tx in history:
                amt_str = f"${tx['amount']:,.2f}" if tx["amount"] > 0 else "-"
                status_color = TerminalColor.GREEN if tx["status"] == "SUCCESS" else TerminalColor.RED
                status_str = f"{status_color}{tx['status']:<9}{TerminalColor.RESET}"
                print(f"  {tx['transaction_id']:<5} | {tx['transaction_type']:<16} | {amt_str:<10} | {status_str} | {tx['timestamp']}")
            print("  " + "-" * 75)
        finally:
            conn.close()

    def handle_change_pin(self) -> None:
        """Handles PIN modification."""
        print("\n  [ CHANGE PIN ]")
        old_pin = prompt_pin("  Enter Current PIN: ")
        new_pin = prompt_pin("  Enter New 4 or 6-digit PIN: ")
        confirm_pin = prompt_pin("  Confirm New PIN: ")

        if new_pin != confirm_pin:
            print(TerminalColor.RED + "  [-] New PIN and confirmation do not match." + TerminalColor.RESET)
            return

        conn = get_db_connection()
        try:
            change_pin(conn, self.account_number, old_pin, new_pin)
            print(TerminalColor.GREEN + "  [+] PIN changed successfully!" + TerminalColor.RESET)
        except AtmBaseException as e:
            print(TerminalColor.RED + f"  [-] PIN change failed: {e.message}" + TerminalColor.RESET)
        finally:
            conn.close()


def admin_menu() -> None:
    """Maintenance and diagnostic admin menu."""
    while True:
        print(TerminalColor.BOLD + "\n  [ SYSTEM ADMINISTRATION & MAINTENANCE ]" + TerminalColor.RESET)
        print("  " + "=" * 45)
        print("  [1] Inspect Vault Cassette Inventory")
        print("  [2] Refill / Set Vault Cassettes")
        print("  [3] View Complete System Audit Ledger")
        print("  [4] Reset Database to Factory Seed State")
        print("  [5] Return to Main Terminal")
        print("  " + "=" * 45)

        adm_choice = input("  Select Admin Option [1-5]: ").strip()

        if adm_choice == "1":
            show_vault_status()
        elif adm_choice == "2":
            print("\n  [ REFILL VAULT CASSETTES ]")
            refills: Dict[int, int] = {}
            for denom in sorted(config.SUPPORTED_DENOMINATIONS, reverse=True):
                raw = input(f"  Set note count for ${denom} cassette: ").strip()
                if raw:
                    try:
                        refills[denom] = int(raw)
                    except ValueError:
                        print(TerminalColor.RED + "  [-] Invalid number." + TerminalColor.RESET)
            if refills:
                conn = get_db_connection()
                try:
                    replenish_vault(conn, refills)
                    print(TerminalColor.GREEN + "  [+] Vault inventory updated successfully!" + TerminalColor.RESET)
                finally:
                    conn.close()
        elif adm_choice == "3":
            conn = get_db_connection()
            try:
                cursor = conn.execute(
                    "SELECT transaction_id, account_number, transaction_type, amount, status, failure_reason, timestamp FROM transactions ORDER BY transaction_id DESC LIMIT 20;"
                )
                rows = cursor.fetchall()
                print(TerminalColor.CYAN + "\n  [ GLOBAL AUDIT LOG (LAST 20 EVENTS) ]" + TerminalColor.RESET)
                print("  " + "-" * 85)
                print(f"  {'ID':<5} | {'Acc #':<7} | {'Type':<16} | {'Amount':<10} | {'Status':<8} | {'Reason':<15} | {'Timestamp'}")
                print("  " + "-" * 85)
                for r in rows:
                    amt_str = f"${r['amount']:,.2f}" if r["amount"] > 0 else "-"
                    reason = r["failure_reason"] or "-"
                    print(f"  {r['transaction_id']:<5} | {r['account_number']:<7} | {r['transaction_type']:<16} | {amt_str:<10} | {r['status']:<8} | {reason:<15} | {r['timestamp']}")
                print("  " + "-" * 85)
            finally:
                conn.close()
        elif adm_choice == "4":
            confirm = input("  Are you sure you want to RESET the entire database? [y/N]: ").strip().lower()
            if confirm == "y":
                seed_data(reset=True)
                print(TerminalColor.GREEN + "  [+] Database reset and seeded successfully!" + TerminalColor.RESET)
        elif adm_choice == "5":
            break


def main() -> None:
    """Primary application execution loop."""
    # Ensure database is seeded on startup if not present
    if not config.DB_PATH.exists():
        seed_data(reset=False)

    print_banner()

    while True:
        print("\n  ╔═══════════════════════════════════════════════════════╗")
        print("  ║                   WELCOME TO THE ATM                  ║")
        print("  ╚═══════════════════════════════════════════════════════╝")
        print("  [1] Insert ATM Card (Login with Account Number & PIN)")
        print("  [2] Check ATM Physical Cash Status")
        print("  [3] System Administrator / Maintenance Tools")
        print("  [4] Exit Simulator")
        print("  " + "-" * 55)

        main_choice = input("  Please select an option [1-4]: ").strip()

        if main_choice == "1":
            acc_num = input("\n  Insert Card (Enter Account Number, e.g., 10001): ").strip()
            if not acc_num:
                print(TerminalColor.RED + "  [-] Account number cannot be blank." + TerminalColor.RESET)
                continue

            pin = prompt_pin("Enter 4-Digit Security PIN: ")

            conn = get_db_connection()
            try:
                account_data = authenticate_user(conn, acc_num, pin)
                print(TerminalColor.GREEN + f"\n  [+] Authentication Successful! Welcome, {account_data['account_holder']}." + TerminalColor.RESET)
                session = AtmSession(account_data["account_number"], account_data["account_holder"])
                session.run_menu()
            except AuthenticationFailedException as e:
                print(TerminalColor.RED + f"\n  [-] Authentication Failed: {e.message}" + TerminalColor.RESET)
            except AccountLockedException as e:
                print(TerminalColor.RED + f"\n  [!] SECURITY ALERT: {e.message}" + TerminalColor.RESET)
            except AccountNotFoundException as e:
                print(TerminalColor.RED + f"\n  [-] Account Error: {e.message}" + TerminalColor.RESET)
            except Exception as e:
                print(TerminalColor.RED + f"\n  [-] Unexpected error: {str(e)}" + TerminalColor.RESET)
            finally:
                conn.close()

        elif main_choice == "2":
            show_vault_status()

        elif main_choice == "3":
            admin_menu()

        elif main_choice == "4":
            print(TerminalColor.CYAN + "\n  [+] Shutting down ATM Simulator. Goodbye!\n" + TerminalColor.RESET)
            break

        else:
            print(TerminalColor.RED + "  [-] Invalid option selected. Please choose 1 - 4." + TerminalColor.RESET)



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  [!] Operation cancelled by user. Exiting safely.")
        sys.exit(0)
