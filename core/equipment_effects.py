"""
Equipment effects — derive bonuses from a creature's currently-equipped items.

Stat bonuses and armor are *derived* every time they're needed (never baked
into the base Stats), so equipping/unequipping can never desync.  Max-HP/mana
bonuses are the exception: those are applied as one-time deltas on equip and
reverted on unequip (see InventorySystem), because current HP/mana is stateful.
"""
from __future__ import annotations
from ecs.world import World
from ecs.component import Equipment, Equippable

ATTRS = ("strength", "dexterity", "constitution",
         "intelligence", "wisdom", "charisma")


def _equipped_equippables(world: World, eid: int):
    eqp = world.get(eid, Equipment)
    if not eqp:
        return
    for slot_eid in eqp.get_all_equipped():
        e = world.get(slot_eid, Equippable)
        if e is not None:
            yield e


def equipped_stat_bonus(world: World, eid: int, attr: str) -> int:
    total = 0
    for e in _equipped_equippables(world, eid):
        if e.stat_bonuses:
            total += e.stat_bonuses.get(attr, 0)
    return total


def effective_value(world: World, eid: int, stats, attr: str) -> int:
    """Base attribute score plus equipment bonuses."""
    base = getattr(stats, attr) if stats else 10
    return base + equipped_stat_bonus(world, eid, attr)


def effective_modifier(world: World, eid: int, stats, attr: str) -> int:
    """D&D-style ability modifier including equipment bonuses."""
    return (effective_value(world, eid, stats, attr) - 10) // 2


def equipped_armor(world: World, eid: int) -> int:
    return sum(e.armor_bonus for e in _equipped_equippables(world, eid))


def equipped_regen(world: World, eid: int) -> int:
    return sum(e.regen for e in _equipped_equippables(world, eid))
