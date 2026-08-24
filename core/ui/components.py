"""
Interactive UI Components: Masked PIN Input, Thermal Receipts,
Formatted Tables, and Dashboard Widgets.
"""

import getpass
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from core.ui.theme import Badge, Box, Color, Gradient, Icon


def prompt_masked_pin(prompt_text: str = "Enter Security PIN: ") -> str:
    """
    Reads a PIN with real-time asterisk / bullet masking (●) and backspace support.
    Supports Windows (msvcrt), POSIX (termios), and automated test piped streams.
    """
    sys.stdout.write(f"  {Color.BOLD}{Color.rgb(0, 242, 254)}{Icon.KEY} {prompt_text}{Color.RESET}")
    sys.stdout.flush()

    if not hasattr(sys.stdin, "isatty") or not sys.stdin.isatty():
        # Fallback for piped input / unit tests
        line = sys.stdin.readline()
        if not line:
            return ""
        return line.strip()

    # Windows Interactive Masking
    if os.name == "nt":
        import msvcrt

        pin_chars: List[str] = []
        while True:
            ch = msvcrt.getch()
            # Enter Key (CR or LF)
            if ch in (b"\r", b"\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                break
            # Backspace Key
            elif ch in (b"\x08", b"\x7f"):
                if pin_chars:
                    pin_chars.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            # Ctrl+C
            elif ch == b"\x03":
                raise KeyboardInterrupt
            # Standard printable character
            else:
                try:
                    char_str = ch.decode("utf-8")
                    if char_str.isprintable():
                        pin_chars.append(char_str)
                        sys.stdout.write(f"{Color.rgb(0, 245, 160)}●{Color.RESET}")
                        sys.stdout.flush()
                except UnicodeDecodeError:
                    pass
        return "".join(pin_chars)
    else:
        # POSIX Interactive Masking
        try:
            import termios
            import tty

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            pin_chars = []
            try:
                tty.setraw(fd)
                while True:
                    ch = sys.stdin.read(1)
                    if ch in ("\r", "\n"):
                        sys.stdout.write("\r\n")
                        sys.stdout.flush()
                        break
                    elif ch in ("\x7f", "\x08"):
                        if pin_chars:
                            pin_chars.pop()
                            sys.stdout.write("\b \b")
                            sys.stdout.flush()
                    elif ch == "\x03":
                        raise KeyboardInterrupt
                    elif ch.isprintable():
                        pin_chars.append(ch)
                        sys.stdout.write(f"{Color.rgb(0, 245, 160)}●{Color.RESET}")
                        sys.stdout.flush()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return "".join(pin_chars)
        except Exception:
            return getpass.getpass("").strip()


class ThermalReceipt:
    """
    Generates authentic, high-contrast thermal paper ATM transaction receipts
    with perforated edges and metadata.
    """

    @staticmethod
    def render(
        title: str,
        account_number: str,
        account_holder: str,
        items: List[Tuple[str, str]],
        footer_note: Optional[str] = None,
    ) -> None:
        width = 54
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n  {Color.DIM}✂ - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -{Color.RESET}")
        print(f"  {Color.rgb(15, 23, 42)}{Color.bg_rgb(241, 245, 249)} ╔{'═' * (width - 2)}╗ {Color.RESET}")
        print(
            f"  {Color.rgb(15, 23, 42)}{Color.bg_rgb(241, 245, 249)} ║{Color.BOLD} {'RESERVE BANK ATM NETWORK'.center(width - 4)} {Color.RESET}{Color.rgb(15, 23, 42)}{Color.bg_rgb(241, 245, 249)}║ {Color.RESET}"
        )
        print(
            f"  {Color.rgb(15, 23, 42)}{Color.bg_rgb(241, 245, 249)} ║ {'TERMINAL ID: #ATM-IND-MUM-042'.center(width - 4)} ║ {Color.RESET}"
        )
        print(
            f"  {Color.rgb(15, 23, 42)}{Color.bg_rgb(241, 245, 249)} ╠{'═' * (width - 2)}╣ {Color.RESET}"
        )
        print(
            f"  {Color.rgb(15, 23, 42)}{Color.bg_rgb(241, 245, 249)} ║ {Color.BOLD}{title.center(width - 4)}{Color.RESET}{Color.rgb(15, 23, 42)}{Color.bg_rgb(241, 245, 249)} ║ {Color.RESET}"
        )
        print(
            f"  {Color.rgb(15, 23, 42)}{Color.bg_rgb(241, 245, 249)} ╟{'─' * (width - 2)}╢ {Color.RESET}"
        )

        # Metadata
        masked_acc = f"•••• •••• {account_number[-4:] if len(account_number) >= 4 else account_number}"
        meta_lines = [
            ("DATE & TIME", timestamp),
            ("CARD NUMBER", masked_acc),
            ("CARDHOLDER", account_holder[:28]),
        ]
        for label, val in meta_lines:
            row_str = f" {label:<16}: {val}"
            print(
                f"  {Color.rgb(15, 23, 42)}{Color.bg_rgb(241, 245, 249)} ║{row_str:<{width - 2}}║ {Color.RESET}"
            )

        print(
            f"  {Color.rgb(15, 23, 42)}{Color.bg_rgb(241, 245, 249)} ╟{'─' * (width - 2)}╢ {Color.RESET}"
        )

        # Dynamic items
        for label, val in items:
            row_str = f" {label:<22} : {val}"
            print(
                f"  {Color.rgb(15, 23, 42)}{Color.bg_rgb(241, 245, 249)} ║{row_str:<{width - 2}}║ {Color.RESET}"
            )

        print(
            f"  {Color.rgb(15, 23, 42)}{Color.bg_rgb(241, 245, 249)} ╟{'─' * (width - 2)}╢ {Color.RESET}"
        )
        print(
            f"  {Color.rgb(15, 23, 42)}{Color.bg_rgb(241, 245, 249)} ║ {'AUTHENTICATION: SHA256 / EMV PIN OK'.center(width - 4)} ║ {Color.RESET}"
        )
        print(
            f"  {Color.rgb(15, 23, 42)}{Color.bg_rgb(241, 245, 249)} ║ {('BARCODE: ' + Icon.BARCODE + ' 0984201').center(width - 4)} ║ {Color.RESET}"
        )
        if footer_note:
            print(
                f"  {Color.rgb(15, 23, 42)}{Color.bg_rgb(241, 245, 249)} ║ {footer_note.center(width - 4)} ║ {Color.RESET}"
            )
        print(f"  {Color.rgb(15, 23, 42)}{Color.bg_rgb(241, 245, 249)} ╚{'═' * (width - 2)}╝ {Color.RESET}")
        print(f"  {Color.DIM}✂ - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -{Color.RESET}\n")


class TableFormatter:
    """Renders formatted Unicode data tables with gradient headers."""

    @staticmethod
    def render_table(
        title: str,
        headers: List[str],
        rows: List[List[Any]],
        alignments: Optional[List[str]] = None,
        col_widths: Optional[List[int]] = None,
    ) -> None:
        num_cols = len(headers)
        if not col_widths:
            widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    clean_len = len(str(cell).split("\033")[0])  # ignore ANSI len
                    widths[i] = max(widths[i], min(clean_len, 35))
        else:
            widths = col_widths

        aligns = alignments or ["left"] * num_cols

        # Header Box
        total_inner_width = sum(widths) + (3 * num_cols) - 1
        print(f"\n  {Color.rgb(0, 242, 254)}╭{'─' * total_inner_width}╮{Color.RESET}")
        print(
            f"  {Color.rgb(0, 242, 254)}│{Color.RESET}{Color.BOLD} {Gradient.cyan_to_emerald(title.center(total_inner_width - 2))} {Color.RESET}{Color.rgb(0, 242, 254)}│{Color.RESET}"
        )
        print(f"  {Color.rgb(0, 242, 254)}├{'┬'.join(['─' * (w + 2) for w in widths])}┤{Color.RESET}")

        # Column Header Row
        header_cells = []
        for i, h in enumerate(headers):
            header_cells.append(f" {Color.BOLD}{h.center(widths[i])}{Color.RESET} ")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}" + f"{Color.rgb(0, 242, 254)}│{Color.RESET}".join(header_cells) + f"{Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}├{'┼'.join(['─' * (w + 2) for w in widths])}┤{Color.RESET}")

        # Data Rows
        if not rows:
            print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET} {'No records found.'.center(total_inner_width - 2)} {Color.rgb(0, 242, 254)}│{Color.RESET}")
        else:
            for row in rows:
                row_cells = []
                for i, cell in enumerate(row):
                    cell_str = str(cell)
                    align = aligns[i]
                    if align == "right":
                        formatted = f" {cell_str:>{widths[i]}} "
                    elif align == "center":
                        formatted = f" {cell_str:^{widths[i]}} "
                    else:
                        formatted = f" {cell_str:<{widths[i]}} "
                    row_cells.append(formatted)
                print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}" + f"{Color.DIM}│{Color.RESET}".join(row_cells) + f"{Color.rgb(0, 242, 254)}│{Color.RESET}")

        print(f"  {Color.rgb(0, 242, 254)}╰{'┴'.join(['─' * (w + 2) for w in widths])}╯{Color.RESET}\n")


class CardWidget:
    """Card widgets for high-level metrics and user dashboards."""

    @staticmethod
    def render_dashboard_card(
        holder: str,
        account_number: str,
        balance: float,
        status: str = "ACTIVE",
    ) -> None:
        width = 60
        status_badge = Badge.active() if status == "ACTIVE" else Badge.locked()

        print(f"\n  {Color.rgb(0, 242, 254)}╭{'─' * (width - 2)}╮{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET} {Icon.CARD} {Color.BOLD}{Gradient.cyan_to_emerald('AUTHENTICATED CARDHOLDER DASHBOARD')}{Color.RESET}{' ' * 13}{Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}├{'─' * (width - 2)}┤{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  Cardholder Name : {Color.BOLD}{holder:<36}{Color.RESET}{Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  Account Number  : {Color.CYAN}{account_number:<36}{Color.RESET}{Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  Available Balance: {Color.rgb(0, 245, 160)}{Color.BOLD}${balance:>12,.2f}{Color.RESET}{' ' * 21}{Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}│{Color.RESET}  Account Status  : {status_badge}{' ' * 27}{Color.rgb(0, 242, 254)}│{Color.RESET}")
        print(f"  {Color.rgb(0, 242, 254)}╰{'─' * (width - 2)}╯{Color.RESET}")
