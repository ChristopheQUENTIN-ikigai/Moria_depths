"""
CharacterView — shows player stats, equipment, and survival status.
"""
from __future__ import annotations
import arcade
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG
from ecs.world import World
from ecs.component import (
    Player, Stats, Health, Mana, SurvivalNeeds, Experience,
    Equipment, Equippable, Item, SpellKnowledge,
)
from core.equipment_effects import effective_value, effective_modifier


class CharacterView(arcade.View):
    def __init__(self, world: World, game_view: arcade.View):
        super().__init__()
        self.world = world
        self.game_view = game_view

    def on_show_view(self):
        self.window.background_color = COLOR_BG

    def on_draw(self):
        self.clear()
        cx = SCREEN_WIDTH // 2

        result = self.world.query_single(
            Player, Stats, Health, Mana, SurvivalNeeds, Experience, Equipment
        )
        if not result:
            return
        _, player, stats, hp, mana, needs, xp, equip = result
        p_eid = result[0]

        arcade.draw_text(
            f"===  {player.name}  ===",
            cx, SCREEN_HEIGHT - 40,
            (200, 180, 120), 22,
            anchor_x="center", bold=True,
        )

        y = SCREEN_HEIGHT - 90
        col1 = 80
        col2 = 400
        col3 = 720

        # ── Stats ──
        arcade.draw_text("ATTRIBUTES", col1, y, (180, 160, 100), 16, bold=True)
        y -= 28
        for attr in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            base = getattr(stats, attr)
            eff = effective_value(self.world, p_eid, stats, attr)
            mod = effective_modifier(self.world, p_eid, stats, attr)
            mod_str = f"+{mod}" if mod >= 0 else str(mod)
            bonus = eff - base
            text = f"{attr[:3].upper()}: {eff} ({mod_str})"
            if bonus > 0:
                text += f"  [+{bonus} gear]"
            color = (140, 220, 140) if bonus > 0 else (180, 180, 180)
            arcade.draw_text(text, col1, y, color, 14)
            y -= 22

        y -= 10
        arcade.draw_text(f"Level: {xp.level}   XP: {xp.xp}/{xp.xp_to_next}", col1, y, (80, 200, 80), 14)
        y -= 22
        arcade.draw_text(f"HP: {hp.current}/{hp.maximum}", col1, y, (200, 80, 80), 14)
        y -= 22
        arcade.draw_text(f"Mana: {mana.current}/{mana.maximum}", col1, y, (80, 80, 200), 14)

        # ── Survival ──
        y2 = SCREEN_HEIGHT - 90
        arcade.draw_text("SURVIVAL", col2, y2, (180, 160, 100), 16, bold=True)
        y2 -= 28
        for label, val in [
            ("Hunger", needs.hunger), ("Thirst", needs.thirst),
            ("Sleep", needs.sleep), ("Stress", needs.stress),
            ("Willpower", needs.willpower),
        ]:
            is_bad = (label != "Stress" and val < 25) or (label == "Stress" and val > 75)
            color = (200, 80, 80) if is_bad else (180, 180, 180)
            arcade.draw_text(f"{label}: {val:.0f}/100", col2, y2, color, 14)
            y2 -= 22

        # ── Equipment ──
        y2 -= 10
        arcade.draw_text("EQUIPMENT", col2, y2, (180, 160, 100), 16, bold=True)
        y2 -= 28
        for slot in equip.slot_names():
            eid = getattr(equip, slot)
            if eid is not None:
                item = self.world.get(eid, Item)
                eq_comp = self.world.get(eid, Equippable)
                name = item.name if item else "???"
                details = ""
                if eq_comp:
                    if eq_comp.damage_dice:
                        dt = "" if eq_comp.damage_type in ("", "physical") else f" {eq_comp.damage_type}"
                        details += f" dmg:{eq_comp.damage_dice}{dt}"
                    if eq_comp.armor_bonus:
                        details += f" armor:+{eq_comp.armor_bonus}"
                    for attr, amt in (eq_comp.stat_bonuses or {}).items():
                        details += f" {attr[:3].upper()}:+{amt}"
                    if eq_comp.max_hp_bonus:
                        details += f" HP:+{eq_comp.max_hp_bonus}"
                    if eq_comp.max_mana_bonus:
                        details += f" MP:+{eq_comp.max_mana_bonus}"
                    if eq_comp.regen:
                        details += f" regen:+{eq_comp.regen}"
                arcade.draw_text(f"{slot:>12}: {name}{details}", col2, y2, (150, 200, 255), 13)
            else:
                arcade.draw_text(f"{slot:>12}: (empty)", col2, y2, (100, 100, 100), 13)
            y2 -= 20

        # ── Known spells ──
        y3 = SCREEN_HEIGHT - 90
        p_eid_result = self.world.query_single(Player, SpellKnowledge)
        if p_eid_result:
            _, _, sk = p_eid_result
            arcade.draw_text("KNOWN SPELLS", col3, y3, (180, 160, 100), 16, bold=True)
            y3 -= 28
            if sk.known_spells:
                for spell_id in sk.known_spells:
                    arcade.draw_text(f"  {spell_id}", col3, y3, (180, 120, 255), 13)
                    y3 -= 20
            else:
                arcade.draw_text("(none)", col3, y3, (100, 100, 100), 13)

        arcade.draw_text("[C / ESC] Close", cx, 30, (120, 120, 140), 12, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.C, arcade.key.ESCAPE):
            self.window.show_view(self.game_view)
