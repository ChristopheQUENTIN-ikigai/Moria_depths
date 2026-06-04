"""
Content registry — loads game data (creatures, items, equipment) from JSON
files in the data/ directory and turns the entries into ECS components.

This is the single source of truth that the map loader and the (future)
in-game editors both read from.  Edit the JSON files in data/ to change the
game's content; no code changes required.
"""
from __future__ import annotations
import json
import os
import random

from ecs.world import World
from ecs.component import (
    Position, Renderable, Blocker, Stats, Health, AI, CreatureType,
    StatusEffects, Equipment, Item, Consumable, Equippable, Ammo,
)
from constants import LAYER_ITEM, LAYER_CREATURE

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Loot rarity → relative spawn weight.
RARITY_WEIGHTS = {
    "common": 100,
    "uncommon": 40,
    "rare": 12,
    "epic": 4,
    "legendary": 1,
}


def _load_json(filename: str, default):
    path = os.path.join(DATA_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"[content] WARNING: could not load {filename}: {exc}")
        return default


def _tuplecolor(entry: dict) -> tuple:
    c = entry.get("color", [255, 255, 255])
    return tuple(c)


# ── Registries (loaded once at import) ───────────────────

CREATURES: dict[str, dict] = _load_json("creatures.json", {})
ITEMS: list[dict] = _load_json("items.json", [])
EQUIPMENT: list[dict] = _load_json("equipment.json", [])
SPELLS: list[dict] = _load_json("spells.json", [])


def reload() -> None:
    """Re-read the JSON files (used by the editors after a save)."""
    global CREATURES, ITEMS, EQUIPMENT, SPELLS
    CREATURES = _load_json("creatures.json", {})
    ITEMS = _load_json("items.json", [])
    EQUIPMENT = _load_json("equipment.json", [])
    SPELLS = _load_json("spells.json", [])


def find_equipment(name: str) -> dict | None:
    for e in EQUIPMENT:
        if e.get("name") == name:
            return e
    return None


def find_item(name: str) -> dict | None:
    for e in ITEMS:
        if e.get("name") == name:
            return e
    return None


# ── Component builders ───────────────────────────────────

def build_consumable(entry: dict) -> Consumable:
    return Consumable(
        effect_type=entry.get("effect_type", ""),
        potency=entry.get("potency", 0),
        hunger_restore=entry.get("hunger_restore", 0.0),
        thirst_restore=entry.get("thirst_restore", 0.0),
        sleep_restore=entry.get("sleep_restore", 0.0),
        stress_reduce=entry.get("stress_reduce", 0.0),
        willpower_restore=entry.get("willpower_restore", 0.0),
        hp_restore=entry.get("hp_restore", 0),
        mana_restore=entry.get("mana_restore", 0),
    )


def build_equippable(entry: dict) -> Equippable:
    return Equippable(
        slot=entry.get("slot", ""),
        armor_bonus=entry.get("armor_bonus", 0),
        damage_dice=entry.get("damage_dice", ""),
        damage_type=entry.get("damage_type", "physical"),
        stat_bonuses=dict(entry.get("stat_bonuses", {})),
        special=entry.get("special", ""),
        ranged=entry.get("ranged", False),
        ammo_type=entry.get("ammo_type", ""),
        max_hp_bonus=entry.get("max_hp_bonus", 0),
        max_mana_bonus=entry.get("max_mana_bonus", 0),
        regen=entry.get("regen", 0),
    )


# ── Spawners (place an entity on the map) ────────────────

def spawn_creature(world: World, x: int, y: int, depth: int, species: str) -> int | None:
    tpl = CREATURES.get(species)
    if tpl is None:
        return None
    e = world.create_entity()
    world.add_component(e, Position(x=x, y=y, depth=depth))
    world.add_component(e, Renderable(
        char=tpl.get("char", "?"), color=_tuplecolor(tpl),
        texture_path=tpl.get("texture", ""), layer=LAYER_CREATURE))
    world.add_component(e, Blocker(blocks_sight=False))
    world.add_component(e, Stats(
        strength=tpl["str"], dexterity=tpl["dex"], constitution=tpl["con"],
        intelligence=tpl["int"], wisdom=tpl["wis"], charisma=tpl["cha"]))
    world.add_component(e, Health(current=tpl["hp"], maximum=tpl["hp"]))
    world.add_component(e, AI(behavior=tpl["behavior"], aggro_range=tpl["aggro"]))
    world.add_component(e, CreatureType(species=species, xp_reward=tpl["xp"]))
    world.add_component(e, StatusEffects())
    we = world.create_entity()
    world.add_component(we, Equippable(slot="weapon", damage_dice=tpl["damage"]))
    world.add_component(e, Equipment(weapon=we))
    return e


def spawn_item_entry(world: World, x: int, y: int, depth: int, entry: dict) -> int:
    """Spawn a consumable or ammo item from an items.json entry."""
    e = world.create_entity()
    world.add_component(e, Position(x=x, y=y, depth=depth))
    kind = entry.get("kind", "consumable")
    if kind == "ammo":
        qty = random.randint(entry.get("qty_min", 5), entry.get("qty_max", 15))
        name = f"{entry['name']} ({qty})"
        world.add_component(e, Item(
            name=name, description=entry.get("description", ""),
            weight=entry.get("weight", 0.5), value=entry.get("value", 5)))
        world.add_component(e, Ammo(ammo_type=entry.get("ammo_type", "arrow"), quantity=qty))
    else:
        world.add_component(e, Item(
            name=entry["name"], description=entry.get("description", ""),
            weight=entry.get("weight", 0.3), value=entry.get("value", 5)))
        world.add_component(e, build_consumable(entry))
    world.add_component(e, Renderable(
        char=entry.get("char", "?"), color=_tuplecolor(entry),
        texture_path=entry.get("texture", ""), layer=LAYER_ITEM))
    return e


def spawn_equipment_entry(world: World, x: int, y: int, depth: int, entry: dict) -> int:
    """Spawn an equippable item (weapon/armor/magic) from an equipment.json entry."""
    e = world.create_entity()
    world.add_component(e, Position(x=x, y=y, depth=depth))
    world.add_component(e, Item(
        name=entry["name"], description=entry.get("description", ""),
        weight=entry.get("weight", 2.0), value=entry.get("value", 10)))
    world.add_component(e, build_equippable(entry))
    world.add_component(e, Renderable(
        char=entry.get("char", "/"), color=_tuplecolor(entry),
        texture_path=entry.get("texture", ""), layer=LAYER_ITEM))
    return e


# ── Depth-weighted loot ──────────────────────────────────

def _weight_for(entry: dict, depth: int) -> float:
    if entry.get("min_depth", 1) > depth:
        return 0.0
    base = RARITY_WEIGHTS.get(entry.get("rarity", "common"), 50)
    # Rarer items become a little more likely the deeper you go.
    if entry.get("rarity") in ("rare", "epic", "legendary"):
        base *= 1.0 + 0.15 * max(0, depth - entry.get("min_depth", 1))
    return base


def random_loot(depth: int) -> tuple[str, dict] | None:
    """Pick a random ('item'|'equipment', entry) weighted by rarity and gated
    by depth. Returns None if nothing is eligible."""
    pool: list[tuple[str, dict, float]] = []
    for entry in ITEMS:
        w = _weight_for(entry, depth)
        if w > 0:
            pool.append(("item", entry, w))
    for entry in EQUIPMENT:
        w = _weight_for(entry, depth)
        if w > 0:
            pool.append(("equipment", entry, w))
    if not pool:
        return None
    weights = [w for _, _, w in pool]
    kind, entry, _ = random.choices(pool, weights=weights, k=1)[0]
    return kind, entry


def spawn_random_loot(world: World, x: int, y: int, depth: int) -> int | None:
    """Spawn one random loot item appropriate to the depth."""
    pick = random_loot(depth)
    if pick is None:
        return None
    kind, entry = pick
    if kind == "item":
        return spawn_item_entry(world, x, y, depth, entry)
    return spawn_equipment_entry(world, x, y, depth, entry)
