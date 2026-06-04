"""
MovementSystem — resolves player movement, door opening (with keys), bump-attack.
"""
from __future__ import annotations
from ecs.world import World
from ecs.component import (
    Position, Player, Blocker, Door, StairsDown, StairsUp,
    Health, AI, Item, Inventory, KeyItem, Renderable,
)
from constants import COLOR_STAIRS_DOWN, COLOR_STAIRS_UP, COLOR_DOOR_OPEN, KEY_COLORS


class MovementSystem:
    def process(self, world: World) -> None:
        intent = world.player_intent
        if not intent or intent[0] != "move":
            return
        _, dx, dy = intent
        result = world.query_single(Player, Position, Inventory)
        if result is None:
            return
        player_eid, _, player_pos, inv = result
        new_x = player_pos.x + dx
        new_y = player_pos.y + dy
        depth = player_pos.depth
        entities_at = world.get_entities_at(new_x, new_y, depth)

        # ── Door interaction ──
        for eid in entities_at:
            door = world.get(eid, Door)
            if door and not door.is_open:
                if door.key_color:
                    # Need matching colored key
                    key_eid = _find_key(world, inv, door.key_color)
                    if key_eid is None:
                        kc = door.key_color.title()
                        world.log(f"The door is locked. You need a {kc} Key.", KEY_COLORS.get(door.key_color, (200,200,100)))
                        world.player_intent = ("done",)
                        return
                    # Consume the key
                    inv.items.remove(key_eid)
                    world.destroy_entity(key_eid)
                    kc = door.key_color.title()
                    world.log(f"You use the {kc} Key to unlock the door.", KEY_COLORS.get(door.key_color, (200,200,100)))
                door.is_open = True
                world.remove_component(eid, Blocker)
                rend = world.get(eid, Renderable)
                if rend:
                    rend.color = COLOR_DOOR_OPEN
                    rend.char = "'"
                    rend.texture_path = "tiles/door_open.jpg"
                if not door.key_color:
                    world.log("You open the door.", (180, 160, 100))
                world.player_intent = ("done",)
                return

        # ── Attack enemy if present ──
        for eid in entities_at:
            if world.has(eid, AI, Health, Position):
                world.player_intent = ("attack", eid)
                return

        # ── Blocked? ──
        if world.is_blocked(new_x, new_y, depth):
            world.player_intent = ("done",)
            return

        # ── Move the player ──
        world.move_entity(player_eid, new_x, new_y)
        world.player_intent = ("done",)

        # ── Auto-pickup gold ──
        from ecs.component import Gold, GoldPouch
        for eid in list(world.get_entities_at(new_x, new_y, depth)):
            gold = world.get(eid, Gold)
            if gold:
                pouch = world.get(player_eid, GoldPouch)
                if pouch:
                    pouch.amount += gold.amount
                    world.log(f"+{gold.amount} gold ({pouch.amount} total)", (255, 215, 0))
                world.destroy_entity(eid)

        # ── Pick up items hint ──
        for eid in world.get_entities_at(new_x, new_y, depth):
            if eid == player_eid:
                continue
            item = world.get(eid, Item)
            if item:
                world.log(f"You see: {item.name}. Press G to pick up.", (200, 200, 150))
                break

        # ── Stairs hint ──
        for eid in world.get_entities_at(new_x, new_y, depth):
            sd = world.get(eid, StairsDown)
            if sd:
                world.log(f"Stairs down (depth {sd.target_depth}). Press '>' to descend.", COLOR_STAIRS_DOWN)
            su = world.get(eid, StairsUp)
            if su:
                world.log(f"Stairs up (depth {su.target_depth}). Press '<' to ascend.", COLOR_STAIRS_UP)


def _find_key(world: World, inv: Inventory, color: str) -> int | None:
    """Find a key of the given color in the player's inventory."""
    for eid in inv.items:
        ki = world.get(eid, KeyItem)
        if ki and ki.color == color:
            return eid
    return None
