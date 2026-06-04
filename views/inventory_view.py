"""
InventoryView — overlay showing player items.
Keys: Up/Down navigate, U use, E equip, D drop, I/ESC close.
"""
from __future__ import annotations
import arcade
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG
from ecs.world import World
from ecs.component import (
    Player, Inventory, Equipment, Item, Consumable, Equippable,
    SpellSource, Ammo, KeyItem,
)


class InventoryView(arcade.View):
    def __init__(self, world: World, game_view: arcade.View):
        super().__init__()
        self.world = world
        self.game_view = game_view
        self.selected = 0

    def on_show_view(self):
        self.window.background_color = COLOR_BG

    def _get_items(self) -> list[tuple[int, Item]]:
        r = self.world.query_single(Player, Inventory)
        if not r:
            return []
        _, _, inv = r
        out = []
        for eid in inv.items:
            item = self.world.get(eid, Item)
            if item:
                out.append((eid, item))
        return out

    def on_draw(self):
        self.clear()
        cx = SCREEN_WIDTH // 2
        arcade.draw_text("===  INVENTORY  ===", cx, SCREEN_HEIGHT - 40,
                         (200, 180, 120), 22, anchor_x="center", bold=True)

        items = self._get_items()
        if not items:
            arcade.draw_text("Your pack is empty.", cx, SCREEN_HEIGHT // 2,
                             (150, 150, 150), 16, anchor_x="center")
        else:
            y = SCREEN_HEIGHT - 90
            for i, (eid, item) in enumerate(items):
                sel = i == self.selected
                prefix = "> " if sel else "  "
                color = (255, 215, 0) if sel else (180, 180, 180)

                tags = []
                eq = self.world.get(eid, Equippable)
                if eq:
                    tags.append(f"[{eq.slot}]")
                    if eq.damage_dice:
                        tags.append(f"dmg:{eq.damage_dice}")
                    if eq.armor_bonus:
                        tags.append(f"armor:+{eq.armor_bonus}")
                    if eq.ranged:
                        tags.append(f"[ranged, needs {eq.ammo_type}]")
                cons = self.world.get(eid, Consumable)
                if cons:
                    parts = []
                    if cons.hunger_restore:
                        parts.append(f"food+{cons.hunger_restore:.0f}")
                    if cons.thirst_restore:
                        parts.append(f"water+{cons.thirst_restore:.0f}")
                    if cons.hp_restore:
                        parts.append(f"hp+{cons.hp_restore}")
                    if cons.mana_restore:
                        parts.append(f"mp+{cons.mana_restore}")
                    if parts:
                        tags.append("[" + ", ".join(parts) + "]")
                    else:
                        tags.append("[consumable]")
                ammo = self.world.get(eid, Ammo)
                if ammo:
                    tags.append(f"[{ammo.ammo_type} x{ammo.quantity}]")
                ki = self.world.get(eid, KeyItem)
                if ki:
                    tags.append(f"[{ki.color} key]")
                ss = self.world.get(eid, SpellSource)
                if ss:
                    tags.append(f"[{ss.source_type}: {ss.spell_id}]")

                info = "  ".join(tags)
                arcade.draw_text(f"{prefix}{item.name}  {info}", 60, y, color, 14)
                y -= 24
                if y < 60:
                    break

        # Show equipped weapon info
        eqr = self.world.query_single(Player, Equipment)
        if eqr:
            _, _, eq = eqr
            wname = "(none)"
            if eq.weapon is not None:
                wi = self.world.get(eq.weapon, Item)
                we = self.world.get(eq.weapon, Equippable)
                if wi:
                    wname = wi.name
                    if we and we.ranged:
                        wname += f" [ranged, {we.ammo_type}]"
            arcade.draw_text(f"Equipped weapon: {wname}", 60, 55, (150, 200, 255), 12)

        arcade.draw_text(
            "[U] Use  [E] Equip  [D] Drop  [I/ESC] Close  |  Equip a weapon to switch to it",
            cx, 30, (120, 120, 140), 11, anchor_x="center")

    def on_key_press(self, key, modifiers):
        items = self._get_items()
        count = len(items)

        if key == arcade.key.UP:
            self.selected = max(0, self.selected - 1)
        elif key == arcade.key.DOWN:
            self.selected = min(count - 1, self.selected + 1) if count else 0
        elif key == arcade.key.U and items:
            eid, _ = items[self.selected]
            self.world.player_intent = ("use_item", eid)
            self.world.process_turn()
            self._clamp_selection()
        elif key == arcade.key.E and items:
            eid, _ = items[self.selected]
            self.world.player_intent = ("equip_item", eid)
            self.world.process_turn()
            self._clamp_selection()
        elif key == arcade.key.D and items:
            eid, _ = items[self.selected]
            self.world.player_intent = ("drop_item", eid)
            self.world.process_turn()
            self._clamp_selection()
        elif key in (arcade.key.I, arcade.key.ESCAPE):
            self.window.show_view(self.game_view)

    def _clamp_selection(self):
        items = self._get_items()
        if self.selected >= len(items):
            self.selected = max(0, len(items) - 1)
