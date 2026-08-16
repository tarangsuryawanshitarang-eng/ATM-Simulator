"""
Customer ATM Terminal Entry Point for the Advanced ATM Simulator.
Provides an institutional-grade, visually stunning 24-bit TrueColor TUI banking experience
with EMV card reading simulations, real-time masked PIN entry, live cash dispensing animations,
and authentic thermal paper receipts.
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
from core.ui import (
    Badge,
    Box,
    CardWidget,
    Color,
    Gradient,
    Icon,
    Style,
    TableFormatter,
    ThermalReceipt,
    animate_card_reading,
    animate_cash_dispensing,
    animate_vault_deposit,
    prompt_masked_pin,
)
from database.connection import get_db_connection
from database.seeder import seed_data


def print_banner() -> None:
    """Displays the Next-Gen Cyber-Fintech ATM Header."""
    banner_raw = r"""
   █████╗ ████████╗███╗   ███╗    ███████╗██╗███╗   ███╗██╗   ██╗██╗      █████╗ ████████╗ ██████╗ ██████╗ 
  ██╔══██╗╚══██╔══╝████╗ ████║    ██╔════╝██║████╗ ████║██║   ██║██║     ██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗
  ███████║   ██║   ██╔████╔██║    ███████╗██║██╔████╔██║██║   ██║██║     ███████║   ██║   ██║   ██║██████╔╝
  ██╔══██║   ██║   ██║╚██╔╝██║    ╚════██║██║██║╚██╔╝██║██║   ██║██║     ██╔══██║   ██║   ██║   ██║██╔══██╗
  ██║  ██║   ██║   ██║ ╚═╝ ██║    ███████║██║██║ ╚═╝ ██║╚██████╔╝███████╗██║  ██║   ██║   ╚██████╔╝██║  ██║
  ╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚═╝    ╚══════╝╚═╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝"""

    lines = banner_raw.strip("\n").split("\n")
    print("")
    for line in lines:
        print("  " + Gradient.cyan_to_emerald(line))

    # System Status Bar
    print(f"\n  {Color.bg_rgb(15, 23, 42)} {Color.rgb(0, 242, 254)}{Color.BOLD} 🏦 RESERVE BANK OF INDIA {Color.RESET} {Color.bg_rgb(15, 23, 42)}{Color.rgb(148, 163, 184)}│ Terminal: #ATM-IND-MUM-042 │ {Badge.active()} │ {Color.rgb(52, 211, 153)}🔒 TLS 1.3 Active{Color.RESET}\n")


class CustomerAtmSession:
    """
    Manages an isolated customer banking session with visual cards and thermal receipts.
    """

    def __init__(self, account_number: str, account_holder: str):
        self.account_number = str(account_number).strip()
        self.account_holder = str(account_holder).strip()

    def run_menu(self) -> None:
        """Customer transaction loop."""
        while True:
            # Query fresh balance for session header
            conn = get_db_connection()
            try:
                current_bal = get_balance(conn, self.account_number)
            except Exception:
                current_bal = 0.0
            finally:
                conn.close()

            CardWidget.render_dashboard_card(
                holder=self.account_holder,
                account_number=self.account_number,
                balance=current_bal,
                status="ACTIVE",
            )

            print(f"  {Color.rgb(0, 242, 254)}╭{'─' * 58}╮{Color.RESET}")
            print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET} {Color.BOLD}SELECT A BANKING TRANSACTION:{Color.RESET}{' ' * 29}{Color.rgb(0, 242, 254)}│{Color.RESET}")
            print(f"  {Color.rgb(0, 242, 254)}├{'─' * 58}┤{Color.RESET}")
            print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  {Color.CYAN}[1]{Color.RESET} 🔍 Balance Inquiry & Mini-Report{' ' * 23}{Color.rgb(0, 242, 254)}│{Color.RESET}")
            print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  {Color.GREEN}[2]{Color.RESET} 💵 Cash Withdrawal (Fast Cash / Custom Amount){' ' * 9}{Color.rgb(0, 242, 254)}│{Color.RESET}")
            print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  {Color.YELLOW}[3]{Color.RESET} 📥 Cash Deposit (Multiples of $100){' ' * 21}{Color.rgb(0, 242, 254)}│{Color.RESET}")
            print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  {Color.MAGENTA}[4]{Color.RESET} 📜 Mini-Statement (Recent Transaction History){' ' * 10}{Color.rgb(0, 242, 254)}│{Color.RESET}")
            print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  {Color.BLUE}[5]{Color.RESET} 🔑 Change Security PIN{' ' * 33}{Color.rgb(0, 242, 254)}│{Color.RESET}")
            print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  {Color.RED}[6]{Color.RESET} ⏏️  Logout & Eject Card{' ' * 34}{Color.rgb(0, 242, 254)}│{Color.RESET}")
            print(f"  {Color.rgb(0, 242, 254)}╰{'─' * 58}╯{Color.RESET}")

            choice = input(f"  {Color.BOLD}{Color.rgb(0, 242, 254)}Select Option [1-6]: {Color.RESET}").strip()

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
                print(f"\n  {Color.rgb(0, 245, 160)}⏏️  Card Ejected. Thank you for banking with Reserve Bank of India, {self.account_holder}!{Color.RESET}\n")
                break
            else:
                print(f"  {Color.RED}✖ Invalid selection. Please choose an option between 1 and 6.{Color.RESET}")

    def handle_balance_inquiry(self) -> None:
        """Queries and presents the cardholder's own account balance."""
        conn = get_db_connection()
        try:
            balance = get_balance(conn, self.account_number)
            ThermalReceipt.render(
                title="ACCOUNT BALANCE INQUIRY",
                account_number=self.account_number,
                account_holder=self.account_holder,
                items=[
                    ("AVAILABLE BALANCE", f"${balance:,.2f}"),
                    ("LEDGER STATUS", "CLEARED & SETTLED"),
                ],
                footer_note="THANK YOU FOR BANKING WITH US",
            )
        except AtmBaseException as e:
            print(f"\n  {Color.RED}✖ Balance inquiry failed: {e.message}{Color.RESET}")
        finally:
            conn.close()

    def handle_withdrawal(self) -> None:
        """Handles fast cash and custom cash withdrawal with physical note animation."""
        print(f"\n  {Color.rgb(0, 242, 254)}╭{'─' * 58}╮{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET} {Icon.MONEY} {Color.BOLD}CASH WITHDRAWAL (MULTI-DENOMINATION DISPENSER){' ' * 8}{Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}├{'─' * 58}┤{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  [1] $100    [2] $200    [3] $500    [4] $1,000            {Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  [5] Custom Amount (Multiples of $100)                     {Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  [6] Cancel & Return to Dashboard                          {Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}╰{'─' * 58}╯{Color.RESET}")

        fast_cash_map = {"1": 100.0, "2": 200.0, "3": 500.0, "4": 1000.0}
        sub_choice = input(f"  {Color.BOLD}Select withdrawal option [1-6]: {Color.RESET}").strip()

        if sub_choice in fast_cash_map:
            amount = fast_cash_map[sub_choice]
        elif sub_choice == "5":
            raw_amt = input("  Enter withdrawal amount (multiples of $100): $").strip()
            try:
                amount = float(raw_amt)
            except ValueError:
                print(f"  {Color.RED}✖ Invalid amount entered. Please enter a valid number.{Color.RESET}")
                return
        elif sub_choice == "6":
            return
        else:
            print(f"  {Color.RED}✖ Invalid withdrawal selection.{Color.RESET}")
            return

        conn = get_db_connection()
        try:
            result = withdraw(conn, self.account_number, amount)

            # Trigger physical cash dispenser animation
            animate_cash_dispensing(result["dispensed_notes"], amount)

            # Build formatted note breakdown
            note_lines = []
            for denom, count in sorted(result["dispensed_notes"].items(), reverse=True):
                note_lines.append(f"{count}x ${denom} (${denom * count:,.2f})")
            note_str = ", ".join(note_lines)

            ThermalReceipt.render(
                title="CASH WITHDRAWAL RECEIPT",
                account_number=self.account_number,
                account_holder=self.account_holder,
                items=[
                    ("TRANSACTION ID", f"#{result['transaction_id']}"),
                    ("WITHDRAWAL AMOUNT", f"${result['amount']:,.2f}"),
                    ("NOTES DISPENSED", note_str),
                    ("REMAINING BALANCE", f"${result['new_balance']:,.2f}"),
                ],
                footer_note="PLEASE RETAIN RECEIPT FOR YOUR RECORDS",
            )
        except (
            InsufficientFundsException,
            AtmCashExhaustedException,
            UnsupportedDenominationException,
            InvalidAmountException,
            AccountLockedException,
        ) as e:
            print(f"\n  {Color.RED}✖ Withdrawal Rejected: {e.message}{Color.RESET}")
        except Exception as e:
            print(f"\n  {Color.RED}✖ System error during withdrawal: {str(e)}{Color.RESET}")
        finally:
            conn.close()

    def handle_deposit(self) -> None:
        """Handles cash deposit with physical vault intake animation."""
        print(f"\n  {Color.rgb(0, 242, 254)}╭{'─' * 58}╮{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET} {Icon.MONEY} {Color.BOLD}CASH DEPOSIT (AUTOMATED NOTE ACCEPTOR){' ' * 16}{Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}╰{'─' * 58}╯{Color.RESET}")

        raw = input("  Enter cash deposit amount in multiples of $100 (or 0 to cancel): $").strip()
        if not raw or raw == "0":
            print(f"  {Color.YELLOW}ℹ Deposit operation cancelled.{Color.RESET}")
            return
        try:
            amount = float(raw)
        except ValueError:
            print(f"  {Color.RED}✖ Invalid amount. Please enter a valid number.{Color.RESET}")
            return

        if amount <= 0 or amount % 100 != 0:
            print(f"  {Color.RED}✖ Deposit amount must be a positive multiple of $100.{Color.RESET}")
            return

        confirm = input(f"  Deposit ${amount:,.2f} into your account? [y/N]: ").strip().lower()
        if confirm != "y":
            print(f"  {Color.YELLOW}ℹ Deposit cancelled by cardholder.{Color.RESET}")
            return

        conn = get_db_connection()
        try:
            animate_vault_deposit(amount)
            result = deposit(conn, self.account_number, amount)

            ThermalReceipt.render(
                title="CASH DEPOSIT RECEIPT",
                account_number=self.account_number,
                account_holder=self.account_holder,
                items=[
                    ("TRANSACTION ID", f"#{result['transaction_id']}"),
                    ("DEPOSITED AMOUNT", f"${result['deposited_amount']:,.2f}"),
                    ("UPDATED BALANCE", f"${result['new_balance']:,.2f}"),
                    ("VAULT STATUS", "ACCEPTED & CREDITED"),
                ],
                footer_note="FUNDS AVAILABLE IMMEDIATELY",
            )
        except AtmBaseException as e:
            print(f"\n  {Color.RED}✖ Deposit Failed: {e.message}{Color.RESET}")
        except Exception as e:
            print(f"\n  {Color.RED}✖ System error during deposit: {str(e)}{Color.RESET}")
        finally:
            conn.close()

    def handle_statement(self) -> None:
        """Displays recent transaction ledger table."""
        conn = get_db_connection()
        try:
            history = get_transaction_history(conn, self.account_number, limit=10)
            rows = []
            for tx in history:
                amt_str = f"${tx['amount']:,.2f}" if tx["amount"] > 0 else "-"
                status_badge = Badge.success("OK") if tx["status"] == "SUCCESS" else Badge.failed(tx["status"])
                rows.append([
                    f"#{tx['transaction_id']}",
                    tx["transaction_type"],
                    amt_str,
                    status_badge,
                    tx["timestamp"],
                ])

            TableFormatter.render_table(
                title=f"MINI-STATEMENT (RECENT ACTIVITY FOR {self.account_holder.upper()})",
                headers=["Tx ID", "Transaction Type", "Amount ($)", "Status", "Timestamp"],
                rows=rows,
                alignments=["center", "left", "right", "center", "center"],
                col_widths=[8, 20, 14, 12, 22],
            )
        finally:
            conn.close()

    def handle_change_pin(self) -> None:
        """Handles PIN update with live real-time bullet masking."""
        print(f"\n  {Color.rgb(0, 242, 254)}╭{'─' * 58}╮{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET} {Icon.KEY} {Color.BOLD}SECURITY PIN UPDATE PROTOCOL{' ' * 27}{Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}╰{'─' * 58}╯{Color.RESET}")

        old_pin = prompt_masked_pin("Enter Current PIN: ")
        new_pin = prompt_masked_pin("Enter New 4 or 6-Digit PIN: ")
        confirm_pin = prompt_masked_pin("Confirm New Security PIN: ")

        if new_pin != confirm_pin:
            print(f"\n  {Color.RED}✖ Error: New PIN and confirmation do not match.{Color.RESET}")
            return

        conn = get_db_connection()
        try:
            change_pin(conn, self.account_number, old_pin, new_pin)
            print(f"\n  {Color.rgb(0, 245, 160)}✔ Security PIN updated successfully with PBKDF2-HMAC-SHA256!{Color.RESET}")
        except AtmBaseException as e:
            print(f"\n  {Color.RED}✖ PIN update failed: {e.message}{Color.RESET}")
        finally:
            conn.close()


def customer_main() -> None:
    """Primary Customer ATM Kiosk execution loop."""
    if not config.DB_PATH.exists():
        seed_data(reset=False)

    print_banner()

    while True:
        print(f"  {Color.rgb(0, 242, 254)}╭{'─' * 58}╮{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET} {Icon.ATM} {Color.BOLD}WELCOME TO THE RESERVE BANK ATM KIOSK{' ' * 18}{Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}├{'─' * 58}┤{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  {Color.GREEN}[1]{Color.RESET} 💳 Insert ATM Card (Login with Account Number & PIN){' ' * 3}{Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  {Color.RED}[2]{Color.RESET} 🚪 Exit ATM Kiosk{' ' * 39}{Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}╰{'─' * 58}╯{Color.RESET}")

        main_choice = input(f"  {Color.BOLD}{Color.rgb(0, 242, 254)}Please select an option [1-2]: {Color.RESET}").strip()

        if main_choice == "1":
            acc_num = input(f"\n  {Icon.CARD} Insert Card (Enter Account Number, e.g., 10001): ").strip()
            if not acc_num:
                print(f"  {Color.RED}✖ Account number cannot be blank.{Color.RESET}")
                continue

            pin = prompt_masked_pin("Enter 4-Digit Security PIN: ")

            conn = get_db_connection()
            try:
                account_data = authenticate_user(conn, acc_num, pin)
                animate_card_reading(account_data["account_holder"])
                session = CustomerAtmSession(account_data["account_number"], account_data["account_holder"])
                session.run_menu()
            except AuthenticationFailedException as e:
                print(f"\n  {Color.RED}✖ Authentication Failed: {e.message}{Color.RESET}")
            except AccountLockedException as e:
                print(f"\n  {Badge.locked()} {Color.RED}SECURITY ALERT: {e.message}{Color.RESET}")
            except AccountNotFoundException as e:
                print(f"\n  {Color.RED}✖ Account Error: {e.message}{Color.RESET}")
            except Exception as e:
                print(f"\n  {Color.RED}✖ Unexpected error: {str(e)}{Color.RESET}")
            finally:
                conn.close()

        elif main_choice == "2":
            print(f"\n  {Color.rgb(0, 242, 254)}✨ Thank you for using our ATM service. Have a wonderful day!{Color.RESET}\n")
            break

        else:
            print(f"  {Color.RED}✖ Invalid option selected. Please choose 1 or 2.{Color.RESET}")


if __name__ == "__main__":
    try:
        customer_main()
    except KeyboardInterrupt:
        print(f"\n\n  {Color.YELLOW}⚠️  ATM transaction cancelled by customer. Exiting safely.{Color.RESET}")
        sys.exit(0)
