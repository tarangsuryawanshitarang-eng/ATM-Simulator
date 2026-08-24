"""
Transaction and Vault Manager Interface Contracts for the Advanced ATM Simulator.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from core.domain.transaction import TransactionRecord


class ITransactionService(ABC):
    """Abstract interface for Core Banking Operations."""

    @abstractmethod
    def check_balance(self, account_number: str) -> float:
        """Queries the current balance of an account."""
        pass

    @abstractmethod
    def withdraw_cash(self, account_number: str, amount: float) -> Dict[str, Any]:
        """Performs atomic withdrawal with physical note deduction."""
        pass

    @abstractmethod
    def deposit_cash(self, account_number: str, amount_or_notes: Any) -> Dict[str, Any]:
        """Performs atomic deposit with physical note addition."""
        pass

    @abstractmethod
    def get_statement(self, account_number: str, limit: int = 10) -> List[TransactionRecord]:
        """Retrieves recent statement activity for an account."""
        pass

    @abstractmethod
    def change_security_pin(
        self, account_number: str, old_pin: str, new_pin: str
    ) -> bool:
        """Validates current PIN and stores updated salted hash."""
        pass


class IVaultManagerService(ABC):
    """Abstract interface for Physical Cash Cassette Inventory Management."""

    @abstractmethod
    def get_inventory(self) -> Dict[int, int]:
        """Returns mapping of denomination to note count."""
        pass

    @abstractmethod
    def get_total_cash(self) -> int:
        """Returns total cash value physically available in ATM."""
        pass

    @abstractmethod
    def solve_dispense(self, amount: int) -> Dict[int, int]:
        """Calculates exact-change note breakdown using backtracking."""
        pass

    @abstractmethod
    def dispense(self, amount: int) -> Dict[int, int]:
        """Calculates allocation and updates physical cassette inventory."""
        pass

    @abstractmethod
    def deposit_notes(self, notes: Dict[int, int]) -> int:
        """Validates note breakdown and increments cassette inventory."""
        pass

    @abstractmethod
    def replenish_vault(self, refill: Dict[int, int]) -> Dict[int, int]:
        """Admin function to set cassette inventory."""
        pass
