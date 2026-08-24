"""
Account Domain Entity for the Advanced ATM Simulator.
Encapsulates account state, balance transitions, and lockout policies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import config
from core.exceptions import (
    AccountLockedException,
    InsufficientFundsException,
    InvalidAmountException,
)


@dataclass
class Account:
    """
    Rich domain entity representing a customer bank account.
    Enforces business invariants internally through encapsulated methods.
    """
    account_number: str
    account_holder: str
    pin_hash: str
    salt: str
    balance: float = 0.0
    is_locked: bool = False
    failed_attempts: int = 0
    created_at: Optional[str] = None

    def __post_init__(self) -> None:
        self.account_number = str(self.account_number).strip()
        self.account_holder = str(self.account_holder).strip()
        self.balance = round(float(self.balance), 2)
        if self.balance < 0.0:
            raise InvalidAmountException("Account balance cannot be negative.")

    def can_withdraw(self, amount: float) -> bool:
        """Checks if the account has sufficient funds and is active."""
        if self.is_locked:
            raise AccountLockedException(f"Account '{self.account_number}' is locked.")
        if amount <= 0:
            raise InvalidAmountException("Withdrawal amount must be greater than zero.")
        return self.balance >= amount

    def apply_withdrawal(self, amount: float) -> float:
        """Deducts balance atomically from entity state and returns the updated balance."""
        if not self.can_withdraw(amount):
            raise InsufficientFundsException(
                f"Insufficient funds. Balance: ${self.balance:.2f}, Requested: ${amount:.2f}."
            )
        self.balance = round(self.balance - amount, 2)
        return self.balance

    def apply_deposit(self, amount: float) -> float:
        """Credits balance atomically to entity state and returns the updated balance."""
        if self.is_locked:
            raise AccountLockedException(f"Account '{self.account_number}' is locked.")
        if amount <= 0:
            raise InvalidAmountException("Deposit amount must be greater than zero.")
        self.balance = round(self.balance + amount, 2)
        return self.balance

    def record_failed_attempt(self, max_allowed: int = config.MAX_FAILED_ATTEMPTS) -> bool:
        """
        Increments failed attempt counter. If threshold is reached, locks account.
        Returns True if account was locked as a result of this attempt.
        """
        self.failed_attempts += 1
        if self.failed_attempts >= max_allowed:
            self.is_locked = True
            return True
        return False

    def reset_failed_attempts(self) -> None:
        """Resets failed attempt counter to zero upon successful authentication."""
        self.failed_attempts = 0

    def unlock(self) -> None:
        """Unlocks the account and resets failed attempt counters."""
        self.is_locked = False
        self.failed_attempts = 0
