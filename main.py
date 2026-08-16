"""
Customer ATM Terminal Entry Point for the Advanced ATM Simulator.
Provides a strictly isolated, secure customer banking experience for cardholders.
Cardholders can ONLY interact with their own account after authentication.
All bank-wide account inquiries, balances, and diagnostics are strictly restricted to admin.py.
"""

import os
import sys
from typing import Dict

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
    get_balance,
    get_transaction_history,
    withdraw,
)
from database.connection import get_db_connection
from database.seeder import seed_data


# ANSI Color Codes for Terminal Styling
class TerminalColor:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def print_banner() -> None:
    """Displays the Customer ATM Header."""
    print(TerminalColor.CYAN + TerminalColor.BOLD + r"""
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║                     24/7 SECURE ATM BANKING KIOSK                     ║
  ║                   Transaction-Safe Multi-Denomination                ║
  ╚═══════════════════════════════════════════════════════════════════════╝
    """ + TerminalColor.RESET)


def prompt_pin(prompt_text: str = "Enter 4-Digit Security PIN: ") -> str:
    """
    Prompts for PIN reliably across all terminal environments without freezing.
    """
    pin = input(f"  {prompt_text}").strip()
    return pin


class CustomerAtmSession:
    """
    Manages an isolated customer session.
    Cardholders can strictly only access and manipulate their own account data.
    """

    def __init__(self, account_number: str, account_holder: str):
        self.account_number = account_number
        self.account_holder = account_holder

    def run_menu(self) -> None:
        """Customer transaction loop."""
        while True:
            print(TerminalColor.BOLD + f"\n  Cardholder: {self.account_holder} | Account: {self.account_number}" + TerminalColor.RESET)
            print("  " + "=" * 48)
            print("  [1] Balance Inquiry")
            print("  [2] Cash Withdrawal (Fast Cash / Custom Amount)")
            print("  [3] Cash Deposit (Insert Physical Notes)")
            print("  [4] Mini-Statement (Your Recent Transactions)")
            print("  [5] Change Security PIN")
            print("  [6] Logout & Eject Card")
            print("  " + "=" * 48)

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
                print(TerminalColor.GREEN + f"\n  [+] Card ejected. Thank you for banking with us, {self.account_holder}!\n" + TerminalColor.RESET)
                break
            else:
                print(TerminalColor.RED + "  [-] Invalid selection. Please choose 1 to 6." + TerminalColor.RESET)

    def handle_balance_inquiry(self) -> None:
        """Queries and presents the cardholder's own account balance."""
        conn = get_db_connection()
        try:
            balance = get_balance(conn, self.account_number)
            print(TerminalColor.GREEN + f"\n  >>> Available Account Balance: ${balance:,.2f}" + TerminalColor.RESET)
        except AtmBaseException as e:
            print(TerminalColor.RED + f"\n  [-] Inquiry failed: {e.message}" + TerminalColor.RESET)
        finally:
            conn.close()

    def handle_withdrawal(self) -> None:
        """Handles fast cash and custom cash withdrawal for the active cardholder."""
        print("\n  [ CASH WITHDRAWAL ]")
        print("  Fast Cash: [1] $100  [2] $200  [3] $500  [4] $1,000  [5] $2,000")
        print("  Custom:    [6] Enter other amount")
        print("  Cancel:    [7] Return to menu")

        fast_cash_map = {"1": 100, "2": 200, "3": 500, "4": 1000, "5": 2000}
        sub_choice = input("  Select withdrawal option [1-7]: ").strip()

        if sub_choice in fast_cash_map:
            amount = float(fast_cash_map[sub_choice])
        elif sub_choice == "6":
            raw_amt = input("  Enter withdrawal amount (multiples of $100): $").strip()
            try:
                amount = float(raw_amt)
            except ValueError:
                print(TerminalColor.RED + "  [-] Invalid amount. Please enter a numeric amount." + TerminalColor.RESET)
                return
        elif sub_choice == "7":
            return
        else:
            print(TerminalColor.RED + "  [-] Invalid selection." + TerminalColor.RESET)
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
        """Handles physical note cash deposit for the active cardholder."""
        print("\n  [ CASH DEPOSIT - NOTE INSERTION ]")
        print("  Please insert accepted physical notes ($500, $200, $100):")
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
                    print(TerminalColor.RED + "  [-] Invalid integer note count." + TerminalColor.RESET)
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
        """Retrieves and displays recent transaction history strictly for this account."""
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
        """Handles PIN modification for the active cardholder."""
        print("\n  [ CHANGE SECURITY PIN ]")
        old_pin = prompt_pin("Enter Current PIN: ")
        new_pin = prompt_pin("Enter New 4 or 6-Digit PIN: ")
        confirm_pin = prompt_pin("Confirm New PIN: ")

        if new_pin != confirm_pin:
            print(TerminalColor.RED + "  [-] New PIN and confirmation do not match." + TerminalColor.RESET)
            return

        conn = get_db_connection()
        try:
            change_pin(conn, self.account_number, old_pin, new_pin)
            print(TerminalColor.GREEN + "  [+] PIN updated successfully!" + TerminalColor.RESET)
        except AtmBaseException as e:
            print(TerminalColor.RED + f"  [-] PIN update failed: {e.message}" + TerminalColor.RESET)
        finally:
            conn.close()


def customer_main() -> None:
    """Primary Customer ATM execution loop."""
    if not config.DB_PATH.exists():
        seed_data(reset=False)

    print_banner()

    while True:
        print("\n  ╔═══════════════════════════════════════════════════════╗")
        print("  ║                   WELCOME TO THE ATM                  ║")
        print("  ╚═══════════════════════════════════════════════════════╝")
        print("  [1] Insert ATM Card (Login with Account Number & PIN)")
        print("  [2] Exit ATM")
        print("  " + "-" * 55)

        main_choice = input("  Please select an option [1-2]: ").strip()

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
                session = CustomerAtmSession(account_data["account_number"], account_data["account_holder"])
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
            print(TerminalColor.CYAN + "\n  [+] Thank you for using our ATM service. Goodbye!\n" + TerminalColor.RESET)
            break

        else:
            print(TerminalColor.RED + "  [-] Invalid option selected. Please choose 1 or 2." + TerminalColor.RESET)


if __name__ == "__main__":
    try:
        customer_main()
    except KeyboardInterrupt:
        print("\n\n  [!] ATM transaction cancelled by customer. Exiting safely.")
        sys.exit(0)
