"""
Dice rolling helpers.

Supports notation like "2d6+3", "1d8", "3d4-1".
"""
from __future__ import annotations
import random
import re

_DICE_RE = re.compile(r"(\d+)d(\d+)([+-]\d+)?")


def roll_dice(notation: str) -> int:
    """Roll dice from a string like '2d6+3'. Returns total."""
    m = _DICE_RE.fullmatch(notation.strip())
    if not m:
        raise ValueError(f"Invalid dice notation: {notation!r}")
    count = int(m.group(1))
    sides = int(m.group(2))
    modifier = int(m.group(3)) if m.group(3) else 0
    total = sum(random.randint(1, sides) for _ in range(count))
    return total + modifier


def roll_d20() -> int:
    return random.randint(1, 20)


def roll_d(sides: int) -> int:
    return random.randint(1, sides)
