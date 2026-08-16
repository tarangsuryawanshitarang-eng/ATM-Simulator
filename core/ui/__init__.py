"""
Next-Generation Terminal User Interface (TUI) Engine for Advanced ATM Simulator.
Provides 24-bit TrueColor ANSI styling, gradients, micro-animations,
masked input controllers, thermal receipts, and visual card widgets.
"""

from core.ui.components import (
    CardWidget,
    TableFormatter,
    ThermalReceipt,
    prompt_masked_pin,
)
from core.ui.effects import (
    animate_card_reading,
    animate_cash_dispensing,
    animate_network_handshake,
    animate_vault_deposit,
)
from core.ui.theme import Badge, Box, Color, Gradient, Icon, Style

__all__ = [
    "Style",
    "Color",
    "Gradient",
    "Box",
    "Badge",
    "Icon",
    "prompt_masked_pin",
    "ThermalReceipt",
    "TableFormatter",
    "CardWidget",
    "animate_card_reading",
    "animate_cash_dispensing",
    "animate_network_handshake",
    "animate_vault_deposit",
]
