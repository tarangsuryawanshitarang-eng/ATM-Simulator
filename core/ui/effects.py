"""
Terminal Micro-Animations and Visual Feedback Effects.
Provides card reading progress bars, cash dispensing visuals,
and cryptographic verification animations.
"""

import sys
import time
from typing import Dict, Optional

from core.ui.theme import Color, Gradient, Icon


def is_interactive() -> bool:
    """Checks if standard output is attached to an interactive terminal."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def animate_card_reading(cardholder: Optional[str] = None) -> None:
    """Simulates high-speed EMV chip reading and credential verification."""
    if not is_interactive():
        return

    frames = [
        "⠋ Reading EMV Chip...",
        "⠙ Decrypting Card Token...",
        "⠹ Verifying Cryptographic Nonce...",
        "⠸ Handshake Complete!",
    ]
    sys.stdout.write("\n")
    for frame in frames:
        sys.stdout.write(f"\r  {Color.rgb(0, 242, 254)}{Icon.CARD} {frame}{Color.RESET}   ")
        sys.stdout.flush()
        time.sleep(0.06)

    sys.stdout.write(f"\r  {Color.rgb(0, 245, 160)}{Icon.CHECK} Card Authenticated Successfully!{Color.RESET}\n\n")
    sys.stdout.flush()


def animate_cash_dispensing(notes: Dict[int, int], total_amount: float) -> None:
    """Displays visual physical note counting and motorized cash shutter ejection."""
    if not is_interactive():
        return

    sys.stdout.write("\n")
    sys.stdout.write(f"  {Color.rgb(253, 200, 48)}{Icon.MONEY} Preparing Cassette Allocation for ${total_amount:,.2f}...{Color.RESET}\n")
    sys.stdout.flush()
    time.sleep(0.08)

    for denom, count in notes.items():
        if count > 0:
            for c in range(1, count + 1):
                sys.stdout.write(f"\r  {Color.rgb(0, 242, 254)}  ├─ Dispensing ${denom} note [{c}/{count}]... 💵{Color.RESET}")
                sys.stdout.flush()
                time.sleep(0.05)
            sys.stdout.write(f"\r  {Color.rgb(0, 245, 160)}  ├─ Dispensed {count}x ${denom} notes ({Icon.CHECK} Verified){Color.RESET}\n")
            sys.stdout.flush()

    sys.stdout.write(f"  {Color.rgb(0, 245, 160)}  ╰─ {Icon.SPARKLES} Cash Slot Shutter Open: Please Collect Your Cash!{Color.RESET}\n\n")
    sys.stdout.flush()
    time.sleep(0.1)


def animate_vault_deposit(amount: float) -> None:
    """Displays visual note validation and physical cassette deposit."""
    if not is_interactive():
        return

    sys.stdout.write("\n")
    sys.stdout.write(f"  {Color.rgb(0, 242, 254)}📥 Depositing ${amount:,.2f} into Physical Vault Cassettes...{Color.RESET}\n")
    sys.stdout.flush()

    stages = [
        "Optical Note Inspection & Counterfeit Check... ✔",
        "Stacking into Multi-Denomination Cassettes... ✔",
        "Updating Encrypted Relational Ledger... ✔",
    ]
    for stage in stages:
        time.sleep(0.07)
        sys.stdout.write(f"  {Color.rgb(0, 245, 160)}  ├─ {stage}{Color.RESET}\n")
        sys.stdout.flush()

    sys.stdout.write(f"  {Color.rgb(0, 245, 160)}  ╰─ {Icon.CHECK} Deposit Complete & Verified!{Color.RESET}\n\n")
    sys.stdout.flush()


def animate_network_handshake() -> None:
    """Brief network security handshake animation."""
    if not is_interactive():
        return
    sys.stdout.write(f"  {Color.DIM}🔒 Establishing TLS 1.3 encrypted session...{Color.RESET}")
    sys.stdout.flush()
    time.sleep(0.08)
    sys.stdout.write(f"\r  {Color.rgb(0, 245, 160)}✔ Encrypted Banking Session Active{Color.RESET}\n")
    sys.stdout.flush()
