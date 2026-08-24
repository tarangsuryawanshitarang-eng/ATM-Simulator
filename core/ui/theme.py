"""
Visual Design System, TrueColor Gradients, and Styling Engine.
Enables high-resolution, institutional-grade ANSI styling for modern terminals.
"""

import os
import sys
from typing import Tuple


class Color:
    """RGB Color constants and TrueColor ANSI formatter."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Hex/RGB Palette Constants
    CYAN_RGB = (0, 242, 254)
    BLUE_RGB = (79, 172, 254)
    EMERALD_RGB = (0, 245, 160)
    PURPLE_RGB = (161, 140, 209)
    GOLD_RGB = (253, 200, 48)
    ORANGE_RGB = (243, 115, 53)
    CRIMSON_RGB = (255, 65, 108)
    SLATE_RGB = (148, 163, 184)
    DARK_BG_RGB = (15, 23, 42)

    # Standard Fallback Colors
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"

    @staticmethod
    def rgb(r: int, g: int, b: int) -> str:
        """Returns TrueColor foreground ANSI escape code."""
        return f"\033[38;2;{r};{g};{b}m"

    @staticmethod
    def bg_rgb(r: int, g: int, b: int) -> str:
        """Returns TrueColor background ANSI escape code."""
        return f"\033[48;2;{r};{g};{b}m"


class Gradient:
    """TrueColor Linear Gradient Text Generator."""

    @staticmethod
    def apply(text: str, start_rgb: Tuple[int, int, int], end_rgb: Tuple[int, int, int]) -> str:
        """
        Interpolates smooth RGB colors across each character of a text string.
        """
        if not text:
            return ""
        length = len(text)
        if length == 1:
            return f"{Color.rgb(*start_rgb)}{text}{Color.RESET}"

        result = []
        r1, g1, b1 = start_rgb
        r2, g2, b2 = end_rgb

        for i, char in enumerate(text):
            factor = i / (length - 1)
            r = int(r1 + (r2 - r1) * factor)
            g = int(g1 + (g2 - g1) * factor)
            b = int(b1 + (b2 - b1) * factor)
            result.append(f"{Color.rgb(r, g, b)}{char}")

        result.append(Color.RESET)
        return "".join(result)

    @classmethod
    def cyan_to_emerald(cls, text: str) -> str:
        return cls.apply(text, (0, 242, 254), (0, 245, 160))

    @classmethod
    def purple_to_cyan(cls, text: str) -> str:
        return cls.apply(text, (196, 113, 237), (18, 194, 233))

    @classmethod
    def gold_to_orange(cls, text: str) -> str:
        return cls.apply(text, (253, 200, 48), (243, 115, 53))

    @classmethod
    def crimson_to_orange(cls, text: str) -> str:
        return cls.apply(text, (255, 65, 108), (255, 117, 140))


class Box:
    """Unicode Box Drawing Character Sets."""

    # Rounded Elegance (Default)
    TOP_LEFT = "╭"
    TOP_RIGHT = "╮"
    BOTTOM_LEFT = "╰"
    BOTTOM_RIGHT = "╯"
    HORIZ = "─"
    VERT = "│"
    T_DOWN = "┬"
    T_UP = "┴"
    T_RIGHT = "├"
    T_LEFT = "┤"
    CROSS = "┼"

    # Double Banking Frame
    DBL_TOP_LEFT = "╔"
    DBL_TOP_RIGHT = "╗"
    DBL_BOTTOM_LEFT = "╚"
    DBL_BOTTOM_RIGHT = "╝"
    DBL_HORIZ = "═"
    DBL_VERT = "║"
    DBL_T_DOWN = "╦"
    DBL_T_UP = "╩"
    DBL_T_RIGHT = "╠"
    DBL_T_LEFT = "╣"


class Icon:
    """Fintech & Banking Unicode Visual Glyphs."""

    ATM = "🏧"
    BANK = "🏦"
    CARD = "💳"
    KEY = "🔑"
    LOCK = "🔒"
    UNLOCK = "🔓"
    SHIELD = "🛡️"
    MONEY = "💵"
    RECEIPT = "🧾"
    LIGHTNING = "⚡"
    CHECK = "✔"
    CROSS = "✖"
    ARROW_RIGHT = "➜"
    DOT = "●"
    SPARKLES = "✨"
    BARCODE = "█║▌║█║▌"


class Badge:
    """Formatted Pill Badges with Glow Highlights."""

    @staticmethod
    def active() -> str:
        return f"{Color.bg_rgb(6, 78, 59)}{Color.rgb(52, 211, 153)}{Color.BOLD} ● ACTIVE {Color.RESET}"

    @staticmethod
    def locked() -> str:
        return f"{Color.bg_rgb(127, 29, 29)}{Color.rgb(248, 113, 113)}{Color.BOLD} 🔒 LOCKED {Color.RESET}"

    @staticmethod
    def success(label: str = "SUCCESS") -> str:
        return f"{Color.bg_rgb(6, 78, 59)}{Color.rgb(52, 211, 153)}{Color.BOLD} ⚡ {label} {Color.RESET}"

    @staticmethod
    def failed(label: str = "REJECTED") -> str:
        return f"{Color.bg_rgb(127, 29, 29)}{Color.rgb(248, 113, 113)}{Color.BOLD} ✖ {label} {Color.RESET}"

    @staticmethod
    def warning(label: str = "ALERT") -> str:
        return f"{Color.bg_rgb(120, 53, 15)}{Color.rgb(251, 191, 36)}{Color.BOLD} ⚠️ {label} {Color.RESET}"

    @staticmethod
    def info(label: str = "INFO") -> str:
        return f"{Color.bg_rgb(30, 58, 138)}{Color.rgb(147, 197, 253)}{Color.BOLD} ℹ {label} {Color.RESET}"


class Style(Color):
    """Convenience alias for backward compatibility."""
    pass
