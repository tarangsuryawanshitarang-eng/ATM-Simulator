"""
Transaction Record Domain Entity for the Advanced ATM Simulator.
Represents an immutable ledger record in the transaction audit log.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TransactionRecord:
    """
    Immutable domain entity representing an entry in the transaction audit ledger.
    """
    account_number: str
    transaction_type: str
    amount: float
    status: str
    failure_reason: Optional[str] = None
    transaction_id: Optional[int] = None
    timestamp: Optional[str] = None
