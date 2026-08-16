"""
Vault Cassette Domain Entity for the Advanced ATM Simulator.
Represents a physical banknote canister / cassette.
"""

from dataclasses import dataclass

import config
from core.exceptions import InvalidAmountException, UnsupportedDenominationException


@dataclass
class VaultCassette:
    """
    Domain entity representing a specific denomination note cassette inside the physical ATM vault.
    """
    denomination: int
    note_count: int

    def __post_init__(self) -> None:
        if self.denomination not in config.SUPPORTED_DENOMINATIONS:
            raise UnsupportedDenominationException(f"Unsupported denomination: ${self.denomination}")
        if self.note_count < 0:
            raise InvalidAmountException(f"Note count cannot be negative for ${self.denomination} cassette.")

    @property
    def subtotal(self) -> int:
        """Returns the total cash value held in this cassette."""
        return self.denomination * self.note_count

    def deduct(self, count: int) -> None:
        """Deducts dispensed notes from cassette inventory."""
        if count < 0:
            raise InvalidAmountException("Deduction count cannot be negative.")
        if count > self.note_count:
            raise InvalidAmountException(
                f"Cannot deduct {count} notes from ${self.denomination} cassette (available: {self.note_count})."
            )
        self.note_count -= count

    def add(self, count: int) -> None:
        """Adds deposited notes into cassette inventory."""
        if count < 0:
            raise InvalidAmountException("Deposit note count cannot be negative.")
        self.note_count += count
