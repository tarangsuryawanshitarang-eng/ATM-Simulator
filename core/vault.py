"""
Cash Cassette and Vault Management Facade for the Advanced ATM Simulator.
Provides backward-compatible functional interfaces delegating to VaultManagerService.
"""

import sqlite3
from typing import Dict

from core.repositories.vault_repo import SqliteVaultRepository
from core.services.vault import VaultManagerService


def _get_vault_service(conn: sqlite3.Connection) -> VaultManagerService:
    repo = SqliteVaultRepository(conn)
    return VaultManagerService(repo)


def get_vault_inventory(conn: sqlite3.Connection) -> Dict[int, int]:
    """Fetches current note counts across all denominations."""
    return _get_vault_service(conn).get_inventory()


def get_total_vault_cash(conn: sqlite3.Connection) -> int:
    """Calculates total cash physically present in the vault."""
    return _get_vault_service(conn).get_total_cash()


def solve_denomination_allocation(amount: int, inventory: Dict[int, int]) -> Dict[int, int]:
    """Pure algorithmic solver for exact-change note breakdown."""
    from unittest.mock import MagicMock
    dummy_repo = MagicMock()
    dummy_repo.get_all_cassettes.return_value = {
        denom: type("CassetteMock", (), {"note_count": count})()
        for denom, count in inventory.items()
    }
    service = VaultManagerService(dummy_repo)
    # Directly call backtracking solver with inventory
    # To support direct call without repo state:
    import config
    from core.exceptions import AtmCashExhaustedException, InvalidAmountException, UnsupportedDenominationException

    if not isinstance(amount, (int, float)) or amount <= 0:
        raise InvalidAmountException("Withdrawal amount must be greater than zero.")
    if int(amount) != amount:
        raise UnsupportedDenominationException("Withdrawal amount cannot contain fractional currency.")

    target = int(amount)
    min_denom = min(config.SUPPORTED_DENOMINATIONS)
    if target % min_denom != 0:
        raise UnsupportedDenominationException(
            f"Amount must be a multiple of the lowest denomination (${min_denom})."
        )

    total_available = sum(denom * count for denom, count in inventory.items())
    if target > total_available:
        raise AtmCashExhaustedException(
            f"ATM cash capacity insufficient. Available: ${total_available}, Requested: ${target}."
        )

    sorted_denoms = sorted(config.SUPPORTED_DENOMINATIONS, reverse=True)

    def backtrack(index: int, remaining: int, current: Dict[int, int]):
        if remaining == 0:
            return current.copy()
        if index >= len(sorted_denoms):
            return None
        denom = sorted_denoms[index]
        available = inventory.get(denom, 0)
        max_needed = remaining // denom
        max_possible = min(available, max_needed)
        for count in range(max_possible, -1, -1):
            if count > 0:
                current[denom] = count
            else:
                current.pop(denom, None)
            res = backtrack(index + 1, remaining - (count * denom), current)
            if res is not None:
                return res
        current.pop(denom, None)
        return None

    allocation = backtrack(0, target, {})
    if allocation is None:
        raise AtmCashExhaustedException(
            f"ATM cannot dispense exact amount (${target}) with current note cassette combination."
        )
    return allocation


def dispense_cash(conn: sqlite3.Connection, amount: int) -> Dict[int, int]:
    """Dispenses cash and updates physical cassette inventory."""
    return _get_vault_service(conn).dispense(amount)


def deposit_notes(conn: sqlite3.Connection, notes: Dict[int, int]) -> int:
    """Accepts notes and updates physical cassette inventory."""
    return _get_vault_service(conn).deposit_notes(notes)


def replenish_vault(conn: sqlite3.Connection, refill: Dict[int, int]) -> Dict[int, int]:
    """Admin utility to refill/set note counts in the vault."""
    return _get_vault_service(conn).replenish_vault(refill)
