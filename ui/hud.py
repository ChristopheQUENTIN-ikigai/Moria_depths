"""
HUD — draws health, mana, survival bars, XP, depth indicator,
and the message log at the bottom of the screen.

Arcade 3.x API:
  draw_lrbt_rectangle_filled(left, right, bottom, top, color)
  draw_lrbt_rectangle_outline(left, right, bottom, top, color, border_width)
  draw_line(x1, y1, x2, y2, color, line_width)
  draw_text(text, x, y, color, font_size, ...)
"""
from __future__ import annotations
from typing import TYPE_CHECKING

import arcade

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, HUD_HEIGHT, HUD_BAR_WIDTH, HUD_BAR_HEIGHT,
    HUD_PADDING, LOG_VISIBLE_LINES,
    COLOR_HP_BAR, COLOR_HP_BG, COLOR_MANA_BAR, COLOR_MANA_BG,
    COLOR_HUNGER_BAR, COLOR_HUNGER_BG, COLOR_THIRST_BAR, COLOR_THIRST_BG,
    COLOR_SLEEP_BAR, COLOR_SLEEP_BG, COLOR_STRESS_BAR, COLOR_STRESS_BG,
    COLOR_WILLPOWER_BAR, COLOR_WILLPOWER_BG, COLOR_XP_BAR, COLOR_XP_BG,
)

if TYPE_CHECKING:
    from ecs.world import World


def draw_hud(world: "World") -> None:
    """Draw the HUD panel at the bottom of the screen."""
    from ecs.component import Player, Health, Mana, SurvivalNeeds, Experience

    # Dark background panel
    arcade.draw_lrbt_rectangle_filled(
        0, SCREEN_WIDTH, 0, HUD_HEIGHT,
        (20, 18, 25, 240),
    )
    # Separator line
    arcade.draw_line(0, HUD_HEIGHT, SCREEN_WIDTH, HUD_HEIGHT, (60, 55, 70), 2)

    result = world.player(Player, Health, Mana, SurvivalNeeds, Experience)
    if not result:
        return
    _, _, hp, mana, needs, xp = result

    x = HUD_PADDING
    y_top = HUD_HEIGHT - HUD_PADDING

    # ── Column 1: HP, Mana, XP ──
    _draw_bar(x, y_top, "HP", hp.current, hp.maximum, COLOR_HP_BAR, COLOR_HP_BG)
    _draw_bar(x, y_top - 22, "MP", mana.current, mana.maximum, COLOR_MANA_BAR, COLOR_MANA_BG)
    _draw_bar(x, y_top - 44, "XP", xp.xp, xp.xp_to_next, COLOR_XP_BAR, COLOR_XP_BG)

    arcade.draw_text(
        f"Lv {xp.level}  Depth {world.current_depth}  Turn {world.turn}",
        x, y_top - 66, (180, 180, 180), 11,
    )

    # ── Column 2: Survival needs ──
    col2_x = HUD_BAR_WIDTH + 60
    _draw_bar(col2_x, y_top, "Hunger", needs.hunger, 100, COLOR_HUNGER_BAR, COLOR_HUNGER_BG)
    _draw_bar(col2_x, y_top - 22, "Thirst", needs.thirst, 100, COLOR_THIRST_BAR, COLOR_THIRST_BG)
    _draw_bar(col2_x, y_top - 44, "Sleep", needs.sleep, 100, COLOR_SLEEP_BAR, COLOR_SLEEP_BG)
    _draw_bar(col2_x, y_top - 66, "Stress", needs.stress, 100, COLOR_STRESS_BAR, COLOR_STRESS_BG)
    _draw_bar(col2_x, y_top - 88, "Will", needs.willpower, 100, COLOR_WILLPOWER_BAR, COLOR_WILLPOWER_BG)

    # ── Column 3: Message log ──
    log_x = (HUD_BAR_WIDTH + 60) * 2 + 20
    log_y = y_top
    recent = world.messages[-(LOG_VISIBLE_LINES):]
    for i, (text, color) in enumerate(recent):
        arcade.draw_text(
            text, log_x, log_y - i * 16,
            color, 10, anchor_x="left",
        )


def _draw_bar(
    x: float, y_top: float, label: str,
    current: float, maximum: float,
    bar_color: tuple, bg_color: tuple,
) -> None:
    """Draw a labeled status bar. y_top is the top edge."""
    ratio = max(0.0, min(1.0, current / maximum)) if maximum > 0 else 0.0
    bar_w = HUD_BAR_WIDTH
    bottom = y_top - HUD_BAR_HEIGHT
    top = y_top

    # Background (left, right, bottom, top)
    arcade.draw_lrbt_rectangle_filled(x, x + bar_w, bottom, top, bg_color)
    # Filled portion
    if ratio > 0:
        arcade.draw_lrbt_rectangle_filled(x, x + bar_w * ratio, bottom, top, bar_color)
    # Border
    arcade.draw_lrbt_rectangle_outline(x, x + bar_w, bottom, top, (100, 100, 100), 1)
    # Label
    arcade.draw_text(
        f"{label}: {int(current)}/{int(maximum)}",
        x + 4, bottom + 2,
        (220, 220, 220), 10,
    )
