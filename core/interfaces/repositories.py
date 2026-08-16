"""
Repository Interface Contracts for the Advanced ATM Simulator.
Defines pure data-access contracts decoupled from any concrete database provider.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from core.domain.account import Account
from core.domain.transaction import TransactionRecord
from core.domain.vault import VaultCassette


class IAccountRepository(ABC):
    """Abstract interface for Account data persistence."""

    @abstractmethod
    def get_by_number(self, account_number: str) -> Optional[Account]:
        """Retrieves an account entity by its unique account number."""
        pass

    @abstractmethod
    def save(self, account: Account) -> None:
        """Persists updates to an existing account entity."""
        pass

    @abstractmethod
    def create(self, account: Account) -> None:
        """Creates a new account in persistent storage."""
        pass

    @abstractmethod
    def delete(self, account_number: str) -> bool:
        """Deletes an account from persistent storage."""
        pass

    @abstractmethod
    def get_all(self) -> List[Account]:
        """Retrieves all accounts for administrative reporting."""
        pass

    @abstractmethod
    def get_locked_accounts(self) -> List[Account]:
        """Retrieves all accounts currently marked as locked."""
        pass

    @abstractmethod
    def get_next_account_number(self) -> str:
        """Determines the next sequential numeric account number."""
        pass


class ITransactionRepository(ABC):
    """Abstract interface for Transaction audit ledger persistence."""

    @abstractmethod
    def record_transaction(self, tx: TransactionRecord) -> int:
        """Appends an immutable audit record and returns the assigned transaction ID."""
        pass

    @abstractmethod
    def get_recent_by_account(self, account_number: str, limit: int = 10) -> List[TransactionRecord]:
        """Retrieves recent transactions for an individual customer account."""
        pass

    @abstractmethod
    def get_global_audit_logs(
        self, tx_type: Optional[str] = None, limit: int = 25
    ) -> List[TransactionRecord]:
        """Retrieves system-wide audit logs, optionally filtered by transaction type."""
        pass


class IVaultRepository(ABC):
    """Abstract interface for Vault Cassette inventory persistence."""

    @abstractmethod
    def get_all_cassettes(self) -> Dict[int, VaultCassette]:
        """Retrieves mapping of denomination to VaultCassette entity."""
        pass

    @abstractmethod
    def save_inventory(self, inventory: Dict[int, int]) -> None:
        """Persists note counts across cassettes."""
        pass

    @abstractmethod
    def replenish(self, refill: Dict[int, int]) -> None:
        """Admin helper to set/replenish note counts."""
        pass
