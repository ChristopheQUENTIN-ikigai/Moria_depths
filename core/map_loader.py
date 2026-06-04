"""
MapLoader — reads level_XX.txt files and spawns tile + creature + item entities.

Creature / item / equipment definitions now live in data/*.json and are loaded
through core.content.  This module owns map *structure* (walls, floors, doors,
stairs, features, the player) and delegates creature & loot spawning to
core.content so the in-game editors and the game read from one source of truth.
"""
from __future__ import annotations
import os
import random

from ecs.world import World
from ecs.component import (
    Position, Renderable, Blocker, Player, Health, Mana, Stats,
    SurvivalNeeds, Experience, FieldOfView, Inventory, Equipment,
    StatusEffects, SpellKnowledge, GoldPouch, Gold,
    Door, StairsDown, StairsUp, Trap, Chest, Fountain, Altar,
    Item, Consumable, Equippable, KeyItem, Ammo,
)
from constants import (
    MAP_CHARS, LAYER_FLOOR, LAYER_ITEM, LAYER_PLAYER,
    COLOR_WALL, COLOR_FLOOR, COLOR_PLAYER,
    COLOR_STAIRS_DOWN, COLOR_STAIRS_UP,
    COLOR_DOOR_CLOSED, COLOR_TRAP, COLOR_CHEST,
    COLOR_FOUNTAIN, COLOR_ALTAR, DEFAULT_FOV_RADIUS,
    KEY_COLORS,
)
from core import content


def load_level(world: World, filepath: str, depth: int) -> tuple[int, int]:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Map file not found: {filepath}")
    with open(filepath, "r") as f:
        lines = f.readlines()
    grid_lines = []
    for line in lines:
        stripped = line.rstrip("\n")
        if stripped.startswith("# ") and not grid_lines:
            continue
        grid_lines.append(stripped)
    while grid_lines and not grid_lines[-1].strip():
        grid_lines.pop()
    map_height = len(grid_lines)
    map_width = max(len(line) for line in grid_lines) if grid_lines else 0
    player_start = None

    for row_idx, line in enumerate(grid_lines):
        y = map_height - 1 - row_idx
        for col_idx, char in enumerate(line):
            x = col_idx
            tile_type = MAP_CHARS.get(char, None)
            if tile_type is None or tile_type == "wall":
                if char == "#":
                    _spawn_wall(world, x, y, depth)
                continue
            _spawn_floor(world, x, y, depth)
            if tile_type == "floor":
                pass
            elif tile_type == "player_start":
                player_start = (x, y)
            elif tile_type == "stairs_down":
                _spawn_stairs_down(world, x, y, depth)
            elif tile_type == "stairs_up":
                _spawn_stairs_up(world, x, y, depth)
            elif tile_type == "door":
                _spawn_door(world, x, y, depth, "")
            elif tile_type.startswith("door_"):
                color = tile_type.split("_", 1)[1]
                _spawn_door(world, x, y, depth, color)
            elif tile_type.startswith("key_"):
                color = tile_type.split("_", 1)[1]
                _spawn_key(world, x, y, depth, color)
            elif tile_type in content.CREATURES:
                content.spawn_creature(world, x, y, depth, tile_type)
            elif tile_type == "item_spawn":
                _spawn_random_item(world, x, y, depth)
            elif tile_type == "trap":
                _spawn_trap(world, x, y, depth)
            elif tile_type == "chest":
                _spawn_chest(world, x, y, depth)
            elif tile_type == "fountain":
                _spawn_fountain(world, x, y, depth)
            elif tile_type == "altar":
                _spawn_altar(world, x, y, depth)
            elif tile_type == "gold_pile":
                _spawn_gold(world, x, y, depth)

    if player_start and not world.query_single(Player):
        _spawn_player(world, player_start[0], player_start[1], depth)
    return map_width, map_height


# ── Loot entry points (kept here for external importers) ──

def _spawn_random_item(w: World, x: int, y: int, d: int):
    """Spawn one depth-appropriate random loot item (delegates to content)."""
    return content.spawn_random_loot(w, x, y, d)


def spawn_creature_loot_gold(w: World, x: int, y: int, d: int, species: str):
    tpl = content.CREATURES.get(species)
    if not tpl:
        return
    if random.random() < 0.6:
        base = tpl["xp"] // 2
        amount = random.randint(max(1, base - 3), base + d * 2)
        _spawn_gold(w, x, y, d, amount)


# ── Tile / structure spawn helpers ───────────────────────

def _spawn_wall(w, x, y, d):
    e = w.create_entity()
    w.add_component(e, Position(x=x, y=y, depth=d))
    w.add_component(e, Renderable(char="#", color=COLOR_WALL, texture_path="tiles/wall_stone.jpg", layer=LAYER_FLOOR))
    w.add_component(e, Blocker(blocks_sight=True))

def _spawn_floor(w, x, y, d):
    e = w.create_entity()
    w.add_component(e, Position(x=x, y=y, depth=d))
    w.add_component(e, Renderable(char=".", color=COLOR_FLOOR, texture_path="tiles/floor_stone.jpg", layer=LAYER_FLOOR))

def _spawn_player(w, x, y, d):
    e = w.create_entity()
    w.add_component(e, Position(x=x, y=y, depth=d))
    w.add_component(e, Renderable(char="@", color=COLOR_PLAYER, texture_path="player/warrior_idle.jpg", layer=LAYER_PLAYER))
    w.add_component(e, Player(name="Adventurer"))
    w.add_component(e, Stats())
    w.add_component(e, Health(current=100, maximum=100))
    w.add_component(e, Mana(current=50, maximum=50))
    w.add_component(e, SurvivalNeeds())
    w.add_component(e, Experience(level=1, xp=0, xp_to_next=100))
    w.add_component(e, FieldOfView(radius=DEFAULT_FOV_RADIUS))
    w.add_component(e, Inventory())
    w.add_component(e, Equipment())
    w.add_component(e, StatusEffects())
    w.add_component(e, SpellKnowledge())
    w.add_component(e, GoldPouch(amount=0))
    w.player_eid = e
    # Starting weapon
    sw = w.create_entity()
    w.add_component(sw, Item(name="Iron Sword", description="A simple iron sword.", weight=3.0, value=15))
    w.add_component(sw, Equippable(slot="weapon", damage_dice="1d6+1", damage_type="physical"))
    w.add_component(sw, Renderable(char="/", color=(180, 180, 200), texture_path="items/weapons/sword.jpg", layer=LAYER_ITEM))
    w.get(e, Equipment).weapon = sw
    # Starting bow + arrows
    bow = w.create_entity()
    w.add_component(bow, Item(name="Short Bow", description="A simple short bow.", weight=2.0, value=20))
    w.add_component(bow, Equippable(slot="weapon", damage_dice="1d6", damage_type="physical", ranged=True, ammo_type="arrow"))
    w.add_component(bow, Renderable(char=")", color=(130, 90, 45), texture_path="items/weapons/bow.jpg", layer=LAYER_ITEM))
    inv = w.get(e, Inventory)
    inv.items.append(bow)
    arrows = w.create_entity()
    w.add_component(arrows, Item(name="Arrows (15)", description="A quiver of arrows.", weight=1.0, value=10))
    w.add_component(arrows, Ammo(ammo_type="arrow", quantity=15))
    w.add_component(arrows, Renderable(char="|", color=(180, 160, 100), layer=LAYER_ITEM))
    inv.items.append(arrows)
    # Starting food & water
    br = w.create_entity()
    w.add_component(br, Item(name="Bread", description="A loaf of bread.", weight=0.3, value=2))
    w.add_component(br, Consumable(effect_type="food", hunger_restore=25.0))
    w.add_component(br, Renderable(char="b", color=(200, 170, 100), texture_path="items/consumables/bread.jpg", layer=LAYER_ITEM))
    inv.items.append(br)
    wf = w.create_entity()
    w.add_component(wf, Item(name="Water Flask", description="A flask of water.", weight=0.5, value=1))
    w.add_component(wf, Consumable(effect_type="drink", thirst_restore=30.0))
    w.add_component(wf, Renderable(char="~", color=(80, 140, 220), texture_path="items/consumables/water_flask.jpg", layer=LAYER_ITEM))
    inv.items.append(wf)
    w.log("You enter the Mines of Moria... Press H for help.", (200, 180, 120))

def _spawn_stairs_down(w, x, y, d):
    e = w.create_entity()
    w.add_component(e, Position(x=x, y=y, depth=d))
    w.add_component(e, Renderable(char=">", color=COLOR_STAIRS_DOWN, texture_path="tiles/stairs_down.jpg", layer=LAYER_FLOOR))
    w.add_component(e, StairsDown(target_depth=d + 1))

def _spawn_stairs_up(w, x, y, d):
    e = w.create_entity()
    w.add_component(e, Position(x=x, y=y, depth=d))
    w.add_component(e, Renderable(char="<", color=COLOR_STAIRS_UP, texture_path="tiles/stairs_up.jpg", layer=LAYER_FLOOR))
    w.add_component(e, StairsUp(target_depth=max(1, d - 1)))

def _spawn_door(w, x, y, d, key_color):
    e = w.create_entity()
    w.add_component(e, Position(x=x, y=y, depth=d))
    color = KEY_COLORS.get(key_color, COLOR_DOOR_CLOSED)
    w.add_component(e, Renderable(char="+", color=color, texture_path="tiles/door_closed.jpg", layer=LAYER_FLOOR))
    w.add_component(e, Door(is_open=False, locked=bool(key_color), key_color=key_color))
    w.add_component(e, Blocker(blocks_sight=True))

def _spawn_key(w, x, y, d, color):
    e = w.create_entity()
    w.add_component(e, Position(x=x, y=y, depth=d))
    kc = KEY_COLORS.get(color, (200, 200, 200))
    w.add_component(e, Renderable(char="k", color=kc, texture_path="items/misc/key.jpg", layer=LAYER_ITEM))
    w.add_component(e, Item(name=f"{color.title()} Key", description=f"A {color} key.", weight=0.1, value=0))
    w.add_component(e, KeyItem(color=color))

def _spawn_trap(w, x, y, d):
    e = w.create_entity()
    w.add_component(e, Position(x=x, y=y, depth=d))
    w.add_component(e, Renderable(char="^", color=COLOR_TRAP, texture_path="tiles/trap_hidden.jpg", layer=LAYER_FLOOR))
    w.add_component(e, Trap(trap_type="spike", damage=10 + d * 2, revealed=False))

def _spawn_chest(w, x, y, d):
    e = w.create_entity()
    w.add_component(e, Position(x=x, y=y, depth=d))
    w.add_component(e, Renderable(char="$", color=COLOR_CHEST, texture_path="tiles/chest.jpg", layer=LAYER_ITEM))
    w.add_component(e, Chest(loot_table_id="common_chest"))

def _spawn_fountain(w, x, y, d):
    e = w.create_entity()
    w.add_component(e, Position(x=x, y=y, depth=d))
    w.add_component(e, Renderable(char="F", color=COLOR_FOUNTAIN, texture_path="tiles/fountain.jpg", layer=LAYER_FLOOR))
    w.add_component(e, Fountain(uses_left=3))

def _spawn_altar(w, x, y, d):
    e = w.create_entity()
    w.add_component(e, Position(x=x, y=y, depth=d))
    w.add_component(e, Renderable(char="A", color=COLOR_ALTAR, texture_path="tiles/altar.jpg", layer=LAYER_FLOOR))
    w.add_component(e, Altar())

def _spawn_gold(w, x, y, d, amount=0):
    if amount <= 0:
        amount = random.randint(3, 10) + d * random.randint(2, 5)
    e = w.create_entity()
    w.add_component(e, Position(x=x, y=y, depth=d))
    w.add_component(e, Renderable(char="$", color=(255, 215, 0), texture_path="items/misc/gold.jpg", layer=LAYER_ITEM))
    w.add_component(e, Gold(amount=amount))
