"""
Customer ATM Terminal Entry Point for the Advanced ATM Simulator.
Provides a strictly isolated, secure customer banking experience for cardholders.
Cardholders can ONLY interact with their own account after authentication.
All bank-wide account inquiries, balances, and diagnostics are strictly restricted to admin.py.
"""

import os
import sys
from typing import Any, Dict

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


# ANSI Color Codes for Tasteful Focal Highlights
class Style:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def print_banner() -> None:
    """Displays the Customer ATM Header."""
    print(Style.CYAN + Style.BOLD + r"""
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║                     24/7 SECURE ATM BANKING KIOSK                     ║
  ║                   Transaction-Safe Multi-Denomination                ║
  ╚═══════════════════════════════════════════════════════════════════════╝
    """ + Style.RESET)


def prompt_pin(prompt_text: str = "Enter 4-Digit Security PIN: ") -> str:
    """Prompts for PIN reliably across all terminal environments."""
    return input(f"  {prompt_text}").strip()


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
            print(f"\n  ┌───────────────────────────────────────────────────────────┐")
            print(f"  │ Cardholder: {self.account_holder:<24} Acc: {self.account_number:<15} │")
            print(f"  ├───────────────────────────────────────────────────────────┤")
            print(f"  │  [1] Balance Inquiry                                      │")
            print(f"  │  [2] Cash Withdrawal (Fast Cash / Custom Amount)          │")
            print(f"  │  [3] Cash Deposit (Fast Deposit / Custom Amount)          │")
            print(f"  │  [4] Mini-Statement (Your Recent Transactions)            │")
            print(f"  │  [5] Change Security PIN                                  │")
            print(f"  │  [6] Logout & Eject Card                                  │")
            print(f"  └───────────────────────────────────────────────────────────┘")

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
                print(Style.GREEN + f"\n  [+] Card ejected. Thank you for banking with us, {self.account_holder}!\n" + Style.RESET)
                break
            else:
                print(Style.RED + "  [-] Invalid selection. Please choose 1 to 6." + Style.RESET)

    def handle_balance_inquiry(self) -> None:
        """Queries and presents the cardholder's own account balance in a clean table."""
        conn = get_db_connection()
        try:
            balance = get_balance(conn, self.account_number)
            print(f"\n  ╔═══════════════════════════════════════════════════════════╗")
            print(f"  ║                    ACCOUNT BALANCE SUMMARY                ║")
            print(f"  ╠═══════════════════════════════════════════════════════════╣")
            print(f"  ║  Account Number : {self.account_number:<39} ║")
            print(f"  ║  Account Holder : {self.account_holder:<39} ║")
            print(f"  ║  Available Funds: {Style.GREEN}${balance:,.2f}{Style.RESET}".ljust(70) + "║")
            print(f"  ╚═══════════════════════════════════════════════════════════╝")
        except AtmBaseException as e:
            print(Style.RED + f"\n  [-] Balance inquiry failed: {e.message}" + Style.RESET)
        finally:
            conn.close()

    def handle_withdrawal(self) -> None:
        """Handles fast cash and custom cash withdrawal for the active cardholder."""
        print("\n  ┌───────────────────────────────────────────────────────────┐")
        print("  │                     CASH WITHDRAWAL                       │")
        print("  ├───────────────────────────────────────────────────────────┤")
        print("  │  Fast Cash: [1] $100   [2] $200   [3] $500   [4] $1,000   │")
        print("  │  Custom:    [5] Enter Other Amount (Multiples of $100)    │")
        print("  │  Cancel:    [6] Return to Main Menu                       │")
        print("  └───────────────────────────────────────────────────────────┘")

        fast_cash_map = {"1": 100, "2": 200, "3": 500, "4": 1000}
        sub_choice = input("  Select withdrawal option [1-6]: ").strip()

        if sub_choice in fast_cash_map:
            amount = float(fast_cash_map[sub_choice])
        elif sub_choice == "5":
            raw_amt = input("  Enter withdrawal amount (multiples of $100): $").strip()
            try:
                amount = float(raw_amt)
            except ValueError:
                print(Style.RED + "  [-] Invalid amount. Please enter a valid numeric amount." + Style.RESET)
                return
        elif sub_choice == "6":
            return
        else:
            print(Style.RED + "  [-] Invalid selection." + Style.RESET)
            return

        conn = get_db_connection()
        try:
            result = withdraw(conn, self.account_number, amount)
            print(f"\n  ╔═══════════════════════════════════════════════════════════╗")
            print(f"  ║              {Style.GREEN}WITHDRAWAL TRANSACTION RECEIPT{Style.RESET}               ║")
            print(f"  ╠═══════════════════════════════════════════════════════════╣")
            print(f"  ║  Transaction ID : #{result['transaction_id']:<38} ║")
            print(f"  ║  Amount Dispensed: {Style.GREEN}${result['amount']:,.2f}{Style.RESET}".ljust(70) + "║")
            print(f"  ╠───────────────────────────────────────────────────────────╣")
            print(f"  ║  Notes Dispensed Breakdown:                               ║")
            for denom, count in sorted(result["dispensed_notes"].items(), reverse=True):
                line = f"  ║    • ${denom:<3} note(s) x {count:<3} = ${denom * count:,.2f}"
                print(line.ljust(62) + "║")
            print(f"  ╠───────────────────────────────────────────────────────────╣")
            print(f"  ║  Remaining Balance: {Style.CYAN}${result['new_balance']:,.2f}{Style.RESET}".ljust(70) + "║")
            print(f"  ╚═══════════════════════════════════════════════════════════╝")
        except (InsufficientFundsException, AtmCashExhaustedException, UnsupportedDenominationException, InvalidAmountException, AccountLockedException) as e:
            print(Style.RED + f"\n  [-] Withdrawal Rejected: {e.message}" + Style.RESET)
        except Exception as e:
            print(Style.RED + f"\n  [-] System error during withdrawal: {str(e)}" + Style.RESET)
        finally:
            conn.close()

    def handle_deposit(self) -> None:
        """Handles simplified cash deposit for the active cardholder."""
        print("\n  ┌───────────────────────────────────────────────────────────┐")
        print("  │                       CASH DEPOSIT                        │")
        print("  ├───────────────────────────────────────────────────────────┤")
        print("  │  Quick Deposit:  [1] $500    [2] $1,000   [3] $2,000      │")
        print("  │  Custom Amount:  [4] Enter Custom Amount                  │")
        print("  │  Cancel:         [5] Return to Main Menu                  │")
        print("  └───────────────────────────────────────────────────────────┘")

        quick_deposit_map = {"1": 500.0, "2": 1000.0, "3": 2000.0}
        choice = input("  Select deposit option [1-5]: ").strip()

        if choice in quick_deposit_map:
            amount = quick_deposit_map[choice]
        elif choice == "4":
            raw = input("  Enter cash deposit amount (multiples of $100): $").strip()
            try:
                amount = float(raw)
            except ValueError:
                print(Style.RED + "  [-] Invalid amount. Please enter a valid number." + Style.RESET)
                return
        elif choice == "5":
            return
        else:
            print(Style.RED + "  [-] Invalid selection." + Style.RESET)
            return

        if amount <= 0 or amount % 100 != 0:
            print(Style.RED + "  [-] Deposit amount must be a positive multiple of $100." + Style.RESET)
            return

        confirm = input(f"  Deposit ${amount:,.2f} into your account? [y/N]: ").strip().lower()
        if confirm != "y":
            print(Style.YELLOW + "  [*] Deposit cancelled." + Style.RESET)
            return

        conn = get_db_connection()
        try:
            result = deposit(conn, self.account_number, amount)
            print(f"\n  ╔═══════════════════════════════════════════════════════════╗")
            print(f"  ║               {Style.GREEN}DEPOSIT TRANSACTION RECEIPT{Style.RESET}                 ║")
            print(f"  ╠═══════════════════════════════════════════════════════════╣")
            print(f"  ║  Transaction ID : #{result['transaction_id']:<38} ║")
            print(f"  ║  Amount Deposited: {Style.GREEN}${result['deposited_amount']:,.2f}{Style.RESET}".ljust(70) + "║")
            print(f"  ║  Updated Balance : {Style.CYAN}${result['new_balance']:,.2f}{Style.RESET}".ljust(70) + "║")
            print(f"  ╚═══════════════════════════════════════════════════════════╝")
        except AtmBaseException as e:
            print(Style.RED + f"\n  [-] Deposit Failed: {e.message}" + Style.RESET)
        except Exception as e:
            print(Style.RED + f"\n  [-] System error during deposit: {str(e)}" + Style.RESET)
        finally:
            conn.close()

    def handle_statement(self) -> None:
        """Retrieves and displays recent transaction history strictly for this account."""
        conn = get_db_connection()
        try:
            history = get_transaction_history(conn, self.account_number, limit=10)
            print(f"\n  ╔═════════════════════════════════════════════════════════════════════════╗")
            print(f"  ║                     MINI-STATEMENT (RECENT ACTIVITY)                    ║")
            print(f"  ╠═══════╦══════════════════╦══════════════╦═════════════╦═════════════════════╣")
            print(f"  ║ Tx ID ║ Transaction Type ║ Amount ($)   ║ Status      ║ Timestamp           ║")
            print(f"  ╠═══════╬══════════════════╬══════════════╬═════════════╬═════════════════════╣")

            if not history:
                print(f"  ║                  No transaction history recorded yet.                  ║")
            else:
                for tx in history:
                    amt_str = f"${tx['amount']:,.2f}" if tx["amount"] > 0 else "-"
                    status_col = Style.GREEN if tx["status"] == "SUCCESS" else Style.RED
                    status_txt = f"{status_col}{tx['status']:<7}{Style.RESET}"
                    print(f"  ║ #{tx['transaction_id']:<5} ║ {tx['transaction_type']:<16} ║ {amt_str:<12} ║ {status_txt} ║ {tx['timestamp']:<19} ║")

            print(f"  ╚═══════╩══════════════════╩══════════════╩═════════════╩═════════════════════╝")
        finally:
            conn.close()

    def handle_change_pin(self) -> None:
        """Handles PIN modification for the active cardholder."""
        print("\n  ┌───────────────────────────────────────────────────────────┐")
        print("  │                   CHANGE SECURITY PIN                     │")
        print("  └───────────────────────────────────────────────────────────┘")
        old_pin = prompt_pin("Enter Current PIN: ")
        new_pin = prompt_pin("Enter New 4 or 6-Digit PIN: ")
        confirm_pin = prompt_pin("Confirm New PIN: ")

        if new_pin != confirm_pin:
            print(Style.RED + "  [-] New PIN and confirmation do not match." + Style.RESET)
            return

        conn = get_db_connection()
        try:
            change_pin(conn, self.account_number, old_pin, new_pin)
            print(Style.GREEN + "\n  [+] Security PIN updated successfully!" + Style.RESET)
        except AtmBaseException as e:
            print(Style.RED + f"\n  [-] PIN update failed: {e.message}" + Style.RESET)
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
                print(Style.RED + "  [-] Account number cannot be blank." + Style.RESET)
                continue

            pin = prompt_pin("Enter 4-Digit Security PIN: ")

            conn = get_db_connection()
            try:
                account_data = authenticate_user(conn, acc_num, pin)
                print(Style.GREEN + f"\n  [+] Authentication Successful! Welcome, {account_data['account_holder']}." + Style.RESET)
                session = CustomerAtmSession(account_data["account_number"], account_data["account_holder"])
                session.run_menu()
            except AuthenticationFailedException as e:
                print(Style.RED + f"\n  [-] Authentication Failed: {e.message}" + Style.RESET)
            except AccountLockedException as e:
                print(Style.RED + f"\n  [!] SECURITY ALERT: {e.message}" + Style.RESET)
            except AccountNotFoundException as e:
                print(Style.RED + f"\n  [-] Account Error: {e.message}" + Style.RESET)
            except Exception as e:
                print(Style.RED + f"\n  [-] Unexpected error: {str(e)}" + Style.RESET)
            finally:
                conn.close()

        elif main_choice == "2":
            print(Style.CYAN + "\n  [+] Thank you for using our ATM service. Goodbye!\n" + Style.RESET)
            break

        else:
            print(Style.RED + "  [-] Invalid option selected. Please choose 1 or 2." + Style.RESET)


if __name__ == "__main__":
    try:
        customer_main()
    except KeyboardInterrupt:
        print("\n\n  [!] ATM transaction cancelled by customer. Exiting safely.")
        sys.exit(0)
