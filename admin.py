"""
Bank Manager & System Administration Portal for the ATM Simulator.
Provides an institutional-grade, visually stunning 24-bit TrueColor TUI for
bank executives to inspect liquidity, manage physical note cassettes,
view security audit ledgers, unlock customer accounts, and inspect cryptographic key derivations.
"""

import os
import sys
from typing import Dict, List, Optional

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
from core.ui import (
    Badge,
    Box,
    CardWidget,
    Color,
    Gradient,
    Icon,
    Style,
    TableFormatter,
)
from core.vault import get_total_vault_cash, get_vault_inventory, replenish_vault
from database.connection import get_db_connection
from database.seeder import seed_data


def print_admin_banner() -> None:
    """Displays the Next-Gen Bank Manager Executive Portal Header."""
    banner_raw = r"""
  ██████╗  █████╗ ███╗   ██╗██╗  ██╗    ███╗   ███╗ █████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗██████╗ 
  ██╔══██╗██╔══██╗████╗  ██║██║ ██╔╝    ████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗
  ██████╔╝███████║██╔██╗ ██║█████═╝     ██╔████╔██║███████║██╔██╗ ██║███████║██║  ███╗█████╗  ██████╔╝
  ██╔══██╗██╔══██║██║╚██╗██║██╔═██╗     ██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██╔══██╗
  ██████╔╝██║  ██║██║ ╚████║██║ ╚██╗    ██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║  ██║
  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝    ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝"""

    lines = banner_raw.strip("\n").split("\n")
    print("")
    for line in lines:
        print("  " + Gradient.gold_to_orange(line))

    # Real-time Executive Metrics Strip
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT COUNT(*) as total, SUM(balance) as liquidity, SUM(is_locked) as locked FROM accounts;")
        row = cursor.fetchone()
        total_accounts = row["total"] or 0
        total_liquidity = row["liquidity"] or 0.0
        locked_accounts = row["locked"] or 0
        vault_cash = get_total_vault_cash(conn)
    except Exception:
        total_accounts = 0
        total_liquidity = 0.0
        locked_accounts = 0
        vault_cash = 0
    finally:
        conn.close()

    print(
        f"\n  {Color.bg_rgb(15, 23, 42)} {Color.rgb(253, 200, 48)}{Color.BOLD} 🏦 EXECUTIVE DASHBOARD {Color.RESET} "
        f"{Color.bg_rgb(15, 23, 42)}{Color.rgb(148, 163, 184)}│ Accounts: {Color.WHITE}{total_accounts}{Color.RESET} "
        f"│ Liquidity: {Color.rgb(52, 211, 153)}${total_liquidity:,.2f}{Color.RESET} "
        f"│ Vault Cash: {Color.CYAN}${vault_cash:,.2f}{Color.RESET} "
        f"│ Locked: {Color.RED if locked_accounts > 0 else Color.GREEN}{locked_accounts}{Color.RESET}{Color.bg_rgb(15, 23, 42)} {Color.RESET}\n"
    )


def view_all_accounts() -> None:
    """
    Displays a comprehensive tabular view of customer accounts.
    Allows searching by account number or customer name.
    """
    conn = get_db_connection()
    try:
        search_query = input(f"  {Color.CYAN}Search accounts by Name or Acc # (or press Enter to view all): {Color.RESET}").strip()
        if search_query:
            cursor = conn.execute(
                """
                SELECT account_number, account_holder, balance, is_locked, failed_attempts, created_at
                FROM accounts
                WHERE account_number LIKE ? OR account_holder LIKE ?
                ORDER BY CAST(account_number AS INTEGER) ASC;
                """,
                (f"%{search_query}%", f"%{search_query}%"),
            )
        else:
            cursor = conn.execute(
                """
                SELECT account_number, account_holder, balance, is_locked, failed_attempts, created_at
                FROM accounts
                ORDER BY CAST(account_number AS INTEGER) ASC;
                """
            )
        accounts = cursor.fetchall()

        rows = []
        for acc in accounts:
            status_badge = Badge.locked() if acc["is_locked"] == 1 else Badge.active()
            rows.append([
                acc["account_number"],
                acc["account_holder"],
                f"${acc['balance']:,.2f}",
                status_badge,
                str(acc["failed_attempts"]),
                acc["created_at"] or "-",
            ])

        total_funds = sum(acc["balance"] for acc in accounts)
        title_suffix = f" (SEARCH: '{search_query}')" if search_query else f" ({len(accounts)} PROFILES)"

        TableFormatter.render_table(
            title=f"BANK CUSTOMER DIRECTORY & ACCOUNTS OVERVIEW{title_suffix}",
            headers=["Acc #", "Account Holder", "Balance ($)", "Status", "Failed PINs", "Created Timestamp"],
            rows=rows,
            alignments=["center", "left", "right", "center", "center", "center"],
            col_widths=[8, 24, 15, 14, 12, 20],
        )
        print(f"  {Color.YELLOW}ℹ Total Matching Accounts: {len(accounts)} | Total Aggregate Funds: ${total_funds:,.2f}{Color.RESET}")
    finally:
        conn.close()


def view_vault_cassettes() -> None:
    """Displays vault note quantities and visual gauge bars."""
    conn = get_db_connection()
    try:
        inventory = get_vault_inventory(conn)
        total_cash = get_total_vault_cash(conn)

        rows = []
        for denom in sorted(config.SUPPORTED_DENOMINATIONS, reverse=True):
            count = inventory.get(denom, 0)
            subtotal = denom * count

            # Visual gauge bar (Max capacity assumed 50 notes for visualization)
            max_capacity = 50
            filled = min(10, int((count / max_capacity) * 10))
            bar = f"{Color.GREEN}{'█' * filled}{Color.DIM}{'░' * (10 - filled)}{Color.RESET}"

            rows.append([
                f"${denom}",
                f"{count} notes",
                bar,
                f"${subtotal:,.2f}",
            ])

        TableFormatter.render_table(
            title="PHYSICAL VAULT CASSETTE INVENTORY & CAPACITY",
            headers=["Denomination", "Note Count", "Cassette Level", "Subtotal ($)"],
            rows=rows,
            alignments=["center", "center", "center", "right"],
            col_widths=[14, 14, 20, 16],
        )
        print(f"  {Color.rgb(0, 245, 160)}✔ Total Vault Cash Available: ${total_cash:,.2f}{Color.RESET}\n")
    finally:
        conn.close()


def refill_vault_cassettes() -> None:
    """Allows administrators to replenish note counts across cassettes."""
    print(f"\n  {Color.rgb(253, 200, 48)}╭{'─' * 58}╮{Color.RESET}")
    print(f"  {Color.rgb(253, 200, 48)}│{Color.RESET} {Icon.MONEY} {Color.BOLD}REPLENISH VAULT CASSETTE INVENTORY{' ' * 21}{Color.rgb(253, 200, 48)}│{Color.RESET}")
    print(f"  {Color.rgb(253, 200, 48)}╰{'─' * 58}╯{Color.RESET}")

    conn = get_db_connection()
    try:
        current_inv = get_vault_inventory(conn)
        refill: Dict[int, int] = {}

        for denom in sorted(config.SUPPORTED_DENOMINATIONS, reverse=True):
            curr = current_inv.get(denom, 0)
            raw = input(f"  Set note count for ${denom} Cassette [Current: {curr}, Press Enter to keep]: ").strip()
            if raw:
                try:
                    cnt = int(raw)
                    if cnt < 0:
                        print(f"  {Color.RED}✖ Note count cannot be negative. Skipping ${denom}.{Color.RESET}")
                        refill[denom] = curr
                    else:
                        refill[denom] = cnt
                except ValueError:
                    print(f"  {Color.RED}✖ Invalid number. Skipping ${denom}.{Color.RESET}")
                    refill[denom] = curr
            else:
                refill[denom] = curr

        replenish_vault(conn, refill)
        new_total = get_total_vault_cash(conn)
        print(f"\n  {Color.rgb(0, 245, 160)}✔ Vault replenished successfully! New Total Cash: ${new_total:,.2f}{Color.RESET}")
    finally:
        conn.close()


def handle_create_account() -> None:
    """
    Handles administrative creation of a new customer account.
    Auto-generates sequential account numbers (highest + 1).
    """
    print(f"\n  {Color.rgb(0, 242, 254)}╭{'─' * 58}╮{Color.RESET}")
    print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET} {Icon.CARD} {Color.BOLD}REGISTER NEW CUSTOMER BANK ACCOUNT{' ' * 21}{Color.rgb(0, 242, 254)}│{Color.RESET}")
    print(f"  {Color.rgb(0, 242, 254)}╰{'─' * 58}╯{Color.RESET}")

    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT account_number FROM accounts WHERE account_number GLOB '[0-9]*' ORDER BY CAST(account_number AS INTEGER) DESC LIMIT 1;"
        )
        row = cursor.fetchone()
        suggested_acc = str(int(row["account_number"]) + 1) if row else "10001"

        print(f"  Auto-Generated Account Number : {Color.BOLD}{Color.CYAN}{suggested_acc}{Color.RESET}")

        holder = input("  Enter Customer Full Name      : ").strip()
        if not holder:
            print(f"  {Color.RED}✖ Customer name cannot be blank.{Color.RESET}")
            return

        pin = input("  Set 4 or 6-Digit Security PIN : ").strip()
        if not (pin.isdigit() and len(pin) in (4, 6)):
            print(f"  {Color.RED}✖ PIN must be exactly 4 or 6 numeric digits.{Color.RESET}")
            return

        pin_confirm = input("  Confirm Security PIN          : ").strip()
        if pin != pin_confirm:
            print(f"  {Color.RED}✖ PIN confirmation does not match.{Color.RESET}")
            return

        new_acc = create_account(conn, suggested_acc, holder, pin, 0.0)

        print(f"\n  {Color.rgb(0, 245, 160)}╭{'─' * 58}╮{Color.RESET}")
        print(f"  {Color.rgb(0, 245, 160)}│{Color.RESET} {Icon.SPARKLES} {Color.BOLD}CUSTOMER ACCOUNT CREATED SUCCESSFULLY{' ' * 18}{Color.rgb(0, 245, 160)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 245, 160)}├{'─' * 58}┤{Color.RESET}")
        print(f"  {Color.rgb(0, 245, 160)}│{Color.RESET}  Account Number : {Color.CYAN}{new_acc['account_number']:<38}{Color.RESET}{Color.rgb(0, 245, 160)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 245, 160)}│{Color.RESET}  Account Holder : {Color.BOLD}{new_acc['account_holder']:<38}{Color.RESET}{Color.rgb(0, 245, 160)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 245, 160)}│{Color.RESET}  Opening Balance: {Color.rgb(0, 245, 160)}${new_acc['balance']:>12,.2f}{Color.RESET}{' ' * 23}{Color.rgb(0, 245, 160)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 245, 160)}│{Color.RESET}  Account Status : {Badge.active()}{' ' * 27}{Color.rgb(0, 245, 160)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 245, 160)}╰{'─' * 58}╯{Color.RESET}")

        print(f"\n  Initial Opening Balance is $0.00.")
        print(f"  [1] Make Opening Cash Deposit (Multiples of $100)")
        print(f"  [2] Finish / Return to Main Manager Menu")
        dep_opt = input("  Select an option [1-2, Default 2]: ").strip()

        if dep_opt == "1":
            dep_raw = input("  Enter deposit amount (multiples of $100): $").strip()
            if dep_raw and dep_raw != "0":
                try:
                    dep_val = float(dep_raw)
                    if dep_val <= 0 or dep_val % 100 != 0:
                        print(f"  {Color.RED}✖ Deposit amount must be a positive multiple of $100.{Color.RESET}")
                    else:
                        dep_res = deposit(conn, new_acc["account_number"], dep_val)
                        print(f"\n  {Color.rgb(0, 245, 160)}✔ Deposited ${dep_val:,.2f} successfully! Updated Balance: ${dep_res['new_balance']:,.2f}{Color.RESET}")
                except ValueError:
                    print(f"  {Color.RED}✖ Invalid amount entered.{Color.RESET}")
    except (AccountAlreadyExistsException, InvalidAmountException, AtmBaseException) as e:
        print(f"\n  {Color.RED}✖ Account Creation Failed: {e.message}{Color.RESET}")
    except Exception as e:
        print(f"\n  {Color.RED}✖ Unexpected error: {str(e)}{Color.RESET}")
    finally:
        conn.close()


def handle_delete_account() -> None:
    """Allows an administrator to close and delete a customer account."""
    print(f"\n  {Color.rgb(255, 65, 108)}╭{'─' * 58}╮{Color.RESET}")
    print(f"  {Color.rgb(255, 65, 108)}│{Color.RESET} 🗑️  {Color.BOLD}CLOSE / DELETE CUSTOMER ACCOUNT{' ' * 24}{Color.rgb(255, 65, 108)}│{Color.RESET}")
    print(f"  {Color.rgb(255, 65, 108)}╰{'─' * 58}╯{Color.RESET}")

    acc_num = input("  Enter Account Number to DELETE (or press Enter to cancel): ").strip()
    if not acc_num:
        print(f"  {Color.YELLOW}ℹ Account deletion cancelled.{Color.RESET}")
        return

    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT account_number, account_holder, balance, is_locked FROM accounts WHERE account_number = ?;",
            (acc_num,),
        )
        row = cursor.fetchone()
        if row is None:
            print(f"\n  {Color.RED}✖ Error: Account '{acc_num}' not found in database.{Color.RESET}")
            return

        status_str = "LOCKED" if row["is_locked"] else "ACTIVE"
        print(f"\n  Account Details for Verification:")
        print(f"    • Account Number : {row['account_number']}")
        print(f"    • Account Holder : {row['account_holder']}")
        print(f"    • Current Balance: ${row['balance']:,.2f}")
        print(f"    • Status         : {status_str}")

        confirm = input(
            f"\n  {Color.RED}{Color.BOLD}Are you sure you want to permanently DELETE account '{acc_num}' ({row['account_holder']})? [y/N]: {Color.RESET}"
        ).strip().lower()

        if confirm != "y":
            print(f"  {Color.YELLOW}ℹ Account deletion aborted by administrator.{Color.RESET}")
            return

        delete_account(conn, acc_num)
        print(f"\n  {Color.rgb(0, 245, 160)}✔ SUCCESS: Account '{acc_num}' ({row['account_holder']}) permanently DELETED.{Color.RESET}")
    except AccountNotFoundException as e:
        print(f"\n  {Color.RED}✖ Error: {e.message}{Color.RESET}")
    except Exception as e:
        print(f"\n  {Color.RED}✖ Unexpected error during deletion: {str(e)}{Color.RESET}")
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
            print(f"\n  {Color.YELLOW}🔒 Currently locked accounts: {locked_list}{Color.RESET}")
        else:
            print(f"\n  {Color.rgb(0, 245, 160)}✔ Notice: No accounts are currently flagged as locked.{Color.RESET}")
    finally:
        conn.close()

    acc_num = input("  Enter Account Number to UNLOCK (or press Enter to cancel): ").strip()
    if not acc_num:
        print(f"  {Color.YELLOW}ℹ Unlock operation cancelled.{Color.RESET}")
        return

    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT account_holder, is_locked FROM accounts WHERE account_number = ?;",
            (acc_num,),
        )
        row = cursor.fetchone()
        if row is None:
            print(f"\n  {Color.RED}✖ Error: Account '{acc_num}' not found in database.{Color.RESET}")
            return

        if row["is_locked"] == 0:
            print(f"\n  {Color.YELLOW}ℹ Account '{acc_num}' ({row['account_holder']}) is already ACTIVE (not locked).{Color.RESET}")
            return

        unlock_account(conn, acc_num)
        print(f"\n  {Color.rgb(0, 245, 160)}✔ SUCCESS: Account '{acc_num}' ({row['account_holder']}) has been UNLOCKED.{Color.RESET}")
    except AccountNotFoundException as e:
        print(f"\n  {Color.RED}✖ Error: {e.message}{Color.RESET}")
    except Exception as e:
        print(f"\n  {Color.RED}✖ Unexpected error: {str(e)}{Color.RESET}")
    finally:
        conn.close()


def handle_crypto_hash_inspector() -> None:
    """
    Live Demonstration & Security Inspector for PBKDF2-HMAC-SHA256 with Pepper & Salt.
    Allows administrators and students to demonstrate modern cryptographic key derivation.
    """
    from core.services.security import Pbkdf2PepperHashProvider

    provider = Pbkdf2PepperHashProvider()

    print(f"\n  {Color.rgb(0, 242, 254)}╭{'─' * 68}╮{Color.RESET}")
    print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET} 🔐 {Color.BOLD}LIVE CRYPTOGRAPHIC HASH & SECURITY INSPECTOR (ACADEMIC DEMO){' ' * 4}{Color.rgb(0, 242, 254)}│{Color.RESET}")
    print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}   PBKDF2-HMAC-SHA256 (100,000 Rounds) + Per-User Salt + Server Pepper  {Color.rgb(0, 242, 254)}│{Color.RESET}")
    print(f"  {Color.rgb(0, 242, 254)}╰{'─' * 68}╯{Color.RESET}")

    test_input = input("  Enter sample PIN or Password to inspect: ").strip()
    if not test_input:
        test_input = "1234"
        print(f"  [Default Sample PIN chosen: {test_input}]")

    salt = provider.generate_salt()
    pepper_secret = provider.default_pepper
    v3_hash = provider.hash_pin(test_input, salt)

    rows = [
        ["Plaintext PIN / Password", test_input, "Never stored in database"],
        ["16-Byte Random Salt", salt, "Unique per-user random entropy"],
        ["Server-Side Pepper", pepper_secret[:24] + "...", "Protects against offline DB leaks"],
        ["PBKDF2 Work Factor", "100,000 Iterations", "HMAC-SHA256 Derived Key"],
        ["Format Identifier", "Version 3 (v3$)", "Institutional Hashing Standard"],
        ["Final Database Hash", v3_hash[:32] + "...", "One-Way Stored Digest"],
    ]

    TableFormatter.render_table(
        title="CRYPTOGRAPHIC DERIVATION PIPELINE BREAKDOWN",
        headers=["Pipeline Stage", "Value / Artifact", "Security Objective"],
        rows=rows,
        alignments=["left", "left", "left"],
        col_widths=[24, 34, 30],
    )

    print(f"  {Color.YELLOW}⚡ Testing Constant-Time Verification against Timing Attacks:{Color.RESET}")
    verify_test = input(f"  Enter PIN to test verification (try '{test_input}' or a wrong PIN): ").strip()
    is_match = provider.verify_pin(verify_test, salt, v3_hash)

    if is_match:
        print(f"  {Color.rgb(0, 245, 160)}✔ Verification Result: TRUE (PIN Matches - Constant-Time check passed){Color.RESET}")
    else:
        print(f"  {Color.RED}✖ Verification Result: FALSE (PIN Mismatch - Access Denied safely){Color.RESET}")

    input("\n  Press Enter to return to Manager Menu...")


def view_audit_logs() -> None:
    """Submenu for viewing global transaction audit trails."""
    while True:
        print(f"\n  {Color.rgb(0, 242, 254)}╭{'─' * 58}╮{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET} 📜 {Color.BOLD}GLOBAL TRANSACTION AUDIT LEDGER{' ' * 24}{Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}├{'─' * 58}┤{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  [1] All Transactions                                   {Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  [2] Cash Withdrawals Only                              {Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  [3] Cash Deposits Only                                 {Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  [4] Security Lockout Events                            {Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  [5] Authentication Attempts                            {Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  [6] Return to Main Manager Menu                        {Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}╰{'─' * 58}╯{Color.RESET}")

        choice = input(f"  {Color.BOLD}Select an audit filter [1-6]: {Color.RESET}").strip()

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
            print(f"  {Color.RED}✖ Invalid filter selection.{Color.RESET}")
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

            table_rows = []
            for r in rows:
                amt_str = f"${r['amount']:,.2f}" if r["amount"] > 0 else "-"
                status_badge = Badge.success("SUCCESS") if r["status"] == "SUCCESS" else Badge.failed(r["status"])
                reason_txt = (r["failure_reason"] or "-")[:18]
                table_rows.append([
                    f"#{r['transaction_id']}",
                    r["account_number"],
                    r["transaction_type"],
                    amt_str,
                    status_badge,
                    reason_txt,
                    r["timestamp"] or "-",
                ])

            TableFormatter.render_table(
                title=f"AUDIT TRAIL: {filter_label}",
                headers=["Tx ID", "Acc #", "Type", "Amount ($)", "Status", "Note / Reason", "Timestamp"],
                rows=table_rows,
                alignments=["center", "center", "left", "right", "center", "left", "center"],
                col_widths=[8, 8, 16, 12, 12, 18, 20],
            )
        finally:
            conn.close()


def reset_database_safely() -> None:
    """Safely handles database reset with a 2-step verification."""
    print(f"\n  {Color.RED}╔═══════════════════════════════════════════════════════════╗")
    print("  ║                   ⚠️  CRITICAL WARNING  ⚠️                  ║")
    print("  ╠═══════════════════════════════════════════════════════════╣")
    print("  ║ This operation will COMPLETELY WIPE all customer balances,║")
    print("  ║ PINs, and transaction audit ledgers, restoring the 100    ║")
    print("  ║ Indian factory seed demo records. CANNOT be undone!       ║")
    print(f"  ╚═══════════════════════════════════════════════════════════╝{Color.RESET}")

    confirm_phrase = input(f"\n  To proceed, please type '{Color.BOLD}CONFIRM RESET{Color.RESET}' (or press Enter to cancel): ").strip()

    if confirm_phrase == "CONFIRM RESET":
        seed_data(reset=True)
        print(f"\n  {Color.rgb(0, 245, 160)}✔ Database reset to factory state with 100 Indian customer accounts.{Color.RESET}")
    else:
        print(f"\n  {Color.YELLOW}ℹ Confirmation phrase did not match. Database reset was ABORTED safely.{Color.RESET}")


def admin_main() -> None:
    """Main execution loop for Bank Manager / Admin Portal."""
    if not config.DB_PATH.exists():
        seed_data(reset=False)

    print_admin_banner()

    while True:
        print(f"  {Color.rgb(253, 200, 48)}╭{'─' * 58}╮{Color.RESET}")
        print(f"  {Color.rgb(253, 200, 48)}│{Color.RESET} {Icon.BANK} {Color.BOLD}BANK MANAGER EXECUTIVE CONTROL PANEL{' ' * 20}{Color.rgb(253, 200, 48)}│{Color.RESET}")
        print(f"  {Color.rgb(253, 200, 48)}├{'─' * 58}┤{Color.RESET}")
        print(f"  {Color.rgb(253, 200, 48)}│{Color.RESET}  {Color.CYAN}[1]{Color.RESET} 🔍 Search & View All Customer Accounts (SQL){' ' * 11}{Color.rgb(253, 200, 48)}│{Color.RESET}")
        print(f"  {Color.rgb(253, 200, 48)}│{Color.RESET}  {Color.GREEN}[2]{Color.RESET} 👤 Open / Register New Customer Account{' ' * 17}{Color.rgb(253, 200, 48)}│{Color.RESET}")
        print(f"  {Color.rgb(253, 200, 48)}│{Color.RESET}  {Color.RED}[3]{Color.RESET} 🗑️  Close / Delete a Customer Account{' ' * 20}{Color.rgb(253, 200, 48)}│{Color.RESET}")
        print(f"  {Color.rgb(253, 200, 48)}│{Color.RESET}  {Color.YELLOW}[4]{Color.RESET} 💵 Inspect Physical Vault Cassette Levels{' ' * 15}{Color.rgb(253, 200, 48)}│{Color.RESET}")
        print(f"  {Color.rgb(253, 200, 48)}│{Color.RESET}  {Color.YELLOW}[5]{Color.RESET} 🔄 Refill / Restock Vault Note Cassettes{' ' * 16}{Color.rgb(253, 200, 48)}│{Color.RESET}")
        print(f"  {Color.rgb(253, 200, 48)}│{Color.RESET}  {Color.GREEN}[6]{Color.RESET} 🔓 Unlock a Locked Customer Account{' ' * 21}{Color.rgb(253, 200, 48)}│{Color.RESET}")
        print(f"  {Color.rgb(253, 200, 48)}│{Color.RESET}  {Color.CYAN}[7]{Color.RESET} 🔐 Cryptographic Hash & Security Inspector (Demo){' ' * 7}{Color.rgb(253, 200, 48)}│{Color.RESET}")
        print(f"  {Color.rgb(253, 200, 48)}│{Color.RESET}  {Color.MAGENTA}[8]{Color.RESET} 📜 Inspect Global Audit & Security Logs{' ' * 17}{Color.rgb(253, 200, 48)}│{Color.RESET}")
        print(f"  {Color.rgb(253, 200, 48)}│{Color.RESET}  {Color.RED}[9]{Color.RESET} ⚠️  Reset Database to Factory Seed (Protected){' ' * 10}{Color.rgb(253, 200, 48)}│{Color.RESET}")
        print(f"  {Color.rgb(253, 200, 48)}│{Color.RESET}  {Color.WHITE}[10]{Color.RESET} 🚪 Exit Admin Portal{' ' * 36}{Color.rgb(253, 200, 48)}│{Color.RESET}")
        print(f"  {Color.rgb(253, 200, 48)}╰{'─' * 58}╯{Color.RESET}")

        choice = input(f"  {Color.BOLD}{Color.rgb(253, 200, 48)}Select an administrative action [1-10]: {Color.RESET}").strip()

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
            print(f"\n  {Color.CYAN}✨ Exiting Admin Portal. Have a great day!{Color.RESET}\n")
            break
        else:
            print(f"  {Color.RED}✖ Invalid selection. Please enter a number between 1 and 10.{Color.RESET}")


if __name__ == "__main__":
    try:
        admin_main()
    except KeyboardInterrupt:
        print(f"\n\n  {Color.YELLOW}⚠️  Admin session cancelled by user. Exiting safely.{Color.RESET}")
        sys.exit(0)
