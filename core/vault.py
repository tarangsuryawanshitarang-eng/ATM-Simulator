"""
Cash Cassette and Vault Management module for the Advanced ATM Simulator.
Implements bounded denomination allocation using deterministic backtracking
and manages physical note inventory state within SQLite transactions.
"""

import sqlite3
from typing import Dict, Optional

import config
from core.exceptions import (
    AtmCashExhaustedException,
    InvalidAmountException,
    UnsupportedDenominationException,
)


def get_vault_inventory(conn: sqlite3.Connection) -> Dict[int, int]:
    """
    Fetches the current physical note inventory from the cash_vault table.
    Returns a dictionary mapping denomination to available note count.
    """
    cursor = conn.execute("SELECT denomination, note_count FROM cash_vault ORDER BY denomination DESC;")
    rows = cursor.fetchall()
    inventory = {row["denomination"]: row["note_count"] for row in rows}
    
    # Ensure all supported denominations are present in dictionary
    for denom in config.SUPPORTED_DENOMINATIONS:
        if denom not in inventory:
            inventory[denom] = 0
    return inventory


def get_total_vault_cash(conn: sqlite3.Connection) -> int:
    """Calculates total monetary value of cash physically present in the vault."""
    inventory = get_vault_inventory(conn)
    return sum(denom * count for denom, count in inventory.items())


def solve_denomination_allocation(amount: int, inventory: Dict[int, int]) -> Dict[int, int]:
    """
    Determines an exact-change note breakdown for the requested amount from physical inventory.
    Uses backtracking with greedy preference (highest denomination first).
    
    Raises:
        InvalidAmountException: if amount <= 0.
        UnsupportedDenominationException: if amount is not divisible by min denomination.
        AtmCashExhaustedException: if physical notes cannot fulfill the exact amount.
    """
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise InvalidAmountException("Withdrawal amount must be greater than zero.")
    
    # Ensure integer amount for physical note dispensing
    if int(amount) != amount:
        raise UnsupportedDenominationException("Withdrawal amount cannot contain fractional currency.")

    target_amount = int(amount)
    min_denom = min(config.SUPPORTED_DENOMINATIONS)

    if target_amount % min_denom != 0:
        raise UnsupportedDenominationException(
            f"Amount must be a multiple of the lowest denomination (${min_denom})."
        )

    total_available = sum(denom * count for denom, count in inventory.items())
    if target_amount > total_available:
        raise AtmCashExhaustedException(
            f"ATM cash capacity insufficient. Available: ${total_available}, Requested: ${target_amount}."
        )

    sorted_denoms = sorted(config.SUPPORTED_DENOMINATIONS, reverse=True)
    
    def backtrack(index: int, remaining: int, current_allocation: Dict[int, int]) -> Optional[Dict[int, int]]:
        if remaining == 0:
            return current_allocation.copy()
        if index >= len(sorted_denoms):
            return None

        denom = sorted_denoms[index]
        available_notes = inventory.get(denom, 0)
        max_needed = remaining // denom
        max_possible = min(available_notes, max_needed)

        # Greedy choice: try largest number of notes first down to 0
        for count in range(max_possible, -1, -1):
            if count > 0:
                current_allocation[denom] = count
            else:
                current_allocation.pop(denom, None)

            result = backtrack(index + 1, remaining - (count * denom), current_allocation)
            if result is not None:
                return result

        current_allocation.pop(denom, None)
        return None

    allocation = backtrack(0, target_amount, {})
    if allocation is None:
        raise AtmCashExhaustedException(
            f"ATM cannot dispense exact amount (${target_amount}) with current note cassette combination."
        )

    return allocation


def dispense_cash(conn: sqlite3.Connection, amount: int) -> Dict[int, int]:
    """
    Computes denomination allocation and updates the physical cash_vault table.
    Must be executed within an active immediate transaction.
    """
    inventory = get_vault_inventory(conn)
    allocation = solve_denomination_allocation(amount, inventory)

    for denom, count in allocation.items():
        conn.execute(
            """
            UPDATE cash_vault 
            SET note_count = note_count - ? 
            WHERE denomination = ?;
            """,
            (count, denom),
        )

    return allocation


def deposit_notes(conn: sqlite3.Connection, notes: Dict[int, int]) -> int:
    """
    Accepts physical notes, validates denominations, and updates cash_vault.
    Returns total monetary value deposited.
    Must be executed within an active immediate transaction.
    """
    if not isinstance(notes, dict) or not notes:
        raise InvalidAmountException("Deposit notes dictionary cannot be empty.")

    total_value = 0
    total_notes_count = 0

    for denom, count in notes.items():
        if denom not in config.SUPPORTED_DENOMINATIONS:
            raise UnsupportedDenominationException(f"Unsupported denomination: ${denom}.")
        if not isinstance(count, int) or count < 0:
            raise InvalidAmountException(f"Invalid note count for denomination ${denom}: {count}.")
        total_value += denom * count
        total_notes_count += count

    if total_notes_count == 0 or total_value <= 0:
        raise InvalidAmountException("Deposit must contain at least one valid note.")

    for denom, count in notes.items():
        if count > 0:
            conn.execute(
                """
                INSERT INTO cash_vault (denomination, note_count)
                VALUES (?, ?)
                ON CONFLICT(denomination) DO UPDATE SET note_count = note_count + excluded.note_count;
                """,
                (denom, count),
            )

    return total_value


def replenish_vault(conn: sqlite3.Connection, refill: Dict[int, int]) -> Dict[int, int]:
    """Admin utility to refill/set note counts in the vault."""
    for denom, count in refill.items():
        if denom in config.SUPPORTED_DENOMINATIONS and count >= 0:
            conn.execute(
                """
                INSERT INTO cash_vault (denomination, note_count)
                VALUES (?, ?)
                ON CONFLICT(denomination) DO UPDATE SET note_count = excluded.note_count;
                """,
                (denom, count),
            )
    return get_vault_inventory(conn)
