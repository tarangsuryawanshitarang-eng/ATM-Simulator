"""
Security and Authentication Interface Contracts for the Advanced ATM Simulator.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from core.domain.account import Account


class IHashProvider(ABC):
    """Abstract interface for Cryptographic Hash Algorithms (Strategy Pattern)."""

    @abstractmethod
    def generate_salt(self) -> str:
        """Generates a cryptographically secure random hexadecimal salt."""
        pass

    @abstractmethod
    def hash_pin(self, pin: str, salt: str, pepper: Optional[str] = None) -> str:
        """Computes a one-way cryptographic digest from PIN, salt, and optional pepper."""
        pass

    @abstractmethod
    def verify_pin(
        self, pin: str, salt: str, expected_hash: str, pepper: Optional[str] = None
    ) -> bool:
        """Verifies if PIN produces expected_hash using timing-safe comparison."""
        pass


class IAuthenticationService(ABC):
    """Abstract interface for User Authentication & Access Control."""

    @abstractmethod
    def authenticate(self, account_number: str, pin: str) -> Account:
        """Authenticates user credentials and manages brute-force attempt counters."""
        pass

    @abstractmethod
    def unlock_account(self, account_number: str) -> bool:
        """Admin function to unlock a locked customer account."""
        pass

    @abstractmethod
    def create_customer_account(
        self, account_holder: str, pin: str, initial_balance: float = 0.0
    ) -> Account:
        """Registers a new customer account with auto-generated account number."""
        pass

    @abstractmethod
    def delete_customer_account(self, account_number: str) -> bool:
        """Closes and deletes a customer account."""
        pass
