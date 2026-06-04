"""
Pathfinding utilities — distance calculation and simple step-toward.
"""
from __future__ import annotations
import math


def bresenham_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Chebyshev distance (max of dx, dy) — good for grid movement."""
    return max(abs(x2 - x1), abs(y2 - y1))


def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    return abs(x2 - x1) + abs(y2 - y1)


def step_toward(
    sx: int, sy: int, tx: int, ty: int, away: bool = False
) -> tuple[int, int]:
    """Return (nx, ny) one step from (sx, sy) toward (or away from) (tx, ty)."""
    dx = tx - sx
    dy = ty - sy

    if away:
        dx = -dx
        dy = -dy

    # Normalize to -1, 0, or 1
    step_x = (1 if dx > 0 else -1) if dx != 0 else 0
    step_y = (1 if dy > 0 else -1) if dy != 0 else 0

    return sx + step_x, sy + step_y
