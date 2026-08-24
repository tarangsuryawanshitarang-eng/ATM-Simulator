"""
Vault Cassette Management and Cash Dispensing Domain Service.
Implements bounded backtracking denomination allocation and inventory state updates.
"""

from typing import Dict, Optional

import config
from core.exceptions import (
    AtmCashExhaustedException,
    InvalidAmountException,
    UnsupportedDenominationException,
)
from core.interfaces.repositories import IVaultRepository
from core.interfaces.transaction import IVaultManagerService


class VaultManagerService(IVaultManagerService):
    """
    Service managing physical ATM vault cassettes and exact-change denomination allocation.
    """

    def __init__(self, vault_repo: IVaultRepository):
        self.vault_repo = vault_repo

    def get_inventory(self) -> Dict[int, int]:
        cassettes = self.vault_repo.get_all_cassettes()
        return {denom: c.note_count for denom, c in cassettes.items()}

    def get_total_cash(self) -> int:
        cassettes = self.vault_repo.get_all_cassettes()
        return sum(c.subtotal for c in cassettes.values())

    def solve_dispense(self, amount: int) -> Dict[int, int]:
        """
        Determines exact-change note breakdown using greedy backtracking solver.
        """
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

        inventory = self.get_inventory()
        total_available = sum(denom * count for denom, count in inventory.items())
        if target > total_available:
            raise AtmCashExhaustedException(
                f"ATM cash capacity insufficient. Available: ${total_available}, Requested: ${target}."
            )

        sorted_denoms = sorted(config.SUPPORTED_DENOMINATIONS, reverse=True)

        def backtrack(
            index: int, remaining: int, current: Dict[int, int]
        ) -> Optional[Dict[int, int]]:
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

                result = backtrack(index + 1, remaining - (count * denom), current)
                if result is not None:
                    return result

            current.pop(denom, None)
            return None

        allocation = backtrack(0, target, {})
        if allocation is None:
            raise AtmCashExhaustedException(
                f"ATM cannot dispense exact amount (${target}) with current note combination."
            )

        return allocation

    def dispense(self, amount: int) -> Dict[int, int]:
        allocation = self.solve_dispense(amount)
        cassettes = self.vault_repo.get_all_cassettes()

        for denom, count in allocation.items():
            cassettes[denom].deduct(count)

        self.vault_repo.save_inventory({d: c.note_count for d, c in cassettes.items()})
        return allocation

    def deposit_notes(self, notes: Dict[int, int]) -> int:
        if not isinstance(notes, dict) or not notes:
            raise InvalidAmountException("Deposit notes cannot be empty.")

        cassettes = self.vault_repo.get_all_cassettes()
        total_value = 0
        total_notes = 0

        for denom, count in notes.items():
            if denom not in config.SUPPORTED_DENOMINATIONS:
                raise UnsupportedDenominationException(f"Unsupported denomination: ${denom}.")
            if not isinstance(count, int) or count < 0:
                raise InvalidAmountException(f"Invalid note count for ${denom}: {count}.")
            total_value += denom * count
            total_notes += count

        if total_notes == 0 or total_value <= 0:
            raise InvalidAmountException("Deposit must contain at least one valid note.")

        for denom, count in notes.items():
            if count > 0:
                cassettes[denom].add(count)

        self.vault_repo.save_inventory({d: c.note_count for d, c in cassettes.items()})
        return total_value

    def replenish_vault(self, refill: Dict[int, int]) -> Dict[int, int]:
        self.vault_repo.replenish(refill)
        return self.get_inventory()
