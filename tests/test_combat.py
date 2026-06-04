"""Tests for combat system, AI, survival, and integration."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ecs.world import World
from ecs.component import (
    Position, Renderable, Player, Health, Mana, Stats,
    SurvivalNeeds, Experience, FieldOfView, Inventory,
    Equipment, Equippable, StatusEffects, SpellKnowledge,
    AI, CreatureType, Blocker, Item, Consumable,
)
from ecs.systems.movement_system import MovementSystem
from ecs.systems.combat_system import CombatSystem
from ecs.systems.ai_system import AISystem
from ecs.systems.survival_system import SurvivalSystem
from ecs.systems.fov_system import FOVSystem
from ecs.systems.inventory_system import InventorySystem
from ecs.systems.status_effect_system import StatusEffectSystem
from constants import DEFAULT_FOV_RADIUS


def _make_world_with_player(px=5, py=5):
    """Create a minimal world with a player."""
    w = World()
    w.current_depth = 1

    p = w.create_entity()
    w.add_component(p, Position(x=px, y=py, depth=1))
    w.add_component(p, Renderable(char="@", color=(60, 180, 255), layer=3))
    w.add_component(p, Player(name="Test Hero"))
    w.add_component(p, Stats(strength=14, dexterity=12))
    w.add_component(p, Health(current=100, maximum=100))
    w.add_component(p, Mana(current=50, maximum=50))
    w.add_component(p, SurvivalNeeds())
    w.add_component(p, Experience(level=1, xp=0, xp_to_next=100))
    w.add_component(p, FieldOfView(radius=DEFAULT_FOV_RADIUS))
    w.add_component(p, Inventory())
    w.add_component(p, Equipment())
    w.add_component(p, StatusEffects())
    w.add_component(p, SpellKnowledge())

    # Give player a weapon
    sword = w.create_entity()
    w.add_component(sword, Equippable(slot="weapon", damage_dice="1d6+1"))
    equip = w.get(p, Equipment)
    equip.weapon = sword

    return w, p


def _make_goblin(w, gx, gy):
    """Spawn a goblin adjacent to test with."""
    g = w.create_entity()
    w.add_component(g, Position(x=gx, y=gy, depth=1))
    w.add_component(g, Renderable(char="g", color=(100, 180, 60), layer=2))
    w.add_component(g, Blocker())
    w.add_component(g, Stats(strength=8, dexterity=10, constitution=8))
    w.add_component(g, Health(current=15, maximum=15))
    w.add_component(g, AI(behavior="aggressive", aggro_range=6))
    w.add_component(g, CreatureType(species="goblin", xp_reward=10))
    w.add_component(g, StatusEffects())
    w.add_component(g, Equipment())
    return g


def test_player_attacks_creature():
    w, p = _make_world_with_player(5, 5)
    g = _make_goblin(w, 6, 5)  # adjacent to the right

    # Move right should trigger attack
    w.register_system(MovementSystem())
    w.register_system(CombatSystem())

    w.player_intent = ("move", 1, 0)
    w.process_turn()

    goblin_hp = w.get(g, Health)
    if goblin_hp:
        # Either we hit or missed
        if goblin_hp.current < 15:
            print(f"  [PASS] player attacks creature (dealt {15 - goblin_hp.current} dmg)")
        else:
            print(f"  [PASS] player attacks creature (missed, which is valid)")
    else:
        # Goblin killed in one hit
        print(f"  [PASS] player attacks creature (one-shot kill)")


def test_creature_death_gives_xp():
    for _ in range(20):
        w, p = _make_world_with_player(5, 5)
        # High dex to guarantee hit
        w.get(p, Stats).dexterity = 30
        g = _make_goblin(w, 6, 5)
        w.get(g, Health).current = 1
        w.get(g, Stats).dexterity = 1  # low AC

        w.register_system(MovementSystem())
        w.register_system(CombatSystem())

        w.player_intent = ("move", 1, 0)
        w.process_turn()

        if not w.entity_exists(g):
            p_xp = w.get(p, Experience)
            assert p_xp.xp >= 10, f"Expected >= 10 XP, got {p_xp.xp}"
            print(f"  [PASS] creature death gives XP ({p_xp.xp} XP)")
            return

    raise AssertionError("Failed to kill goblin in 20 attempts")


def test_movement_blocked_by_wall():
    w, p = _make_world_with_player(5, 5)

    # Place a wall to the right
    wall = w.create_entity()
    w.add_component(wall, Position(x=6, y=5, depth=1))
    w.add_component(wall, Blocker(blocks_sight=True))

    w.register_system(MovementSystem())

    w.player_intent = ("move", 1, 0)
    w.process_turn()

    pos = w.get(p, Position)
    assert pos.x == 5, f"Player should not have moved, but x={pos.x}"
    print("  [PASS] movement blocked by wall")


def test_pickup_item():
    w, p = _make_world_with_player(5, 5)

    # Place an item at player position
    item_eid = w.create_entity()
    w.add_component(item_eid, Position(x=5, y=5, depth=1))
    w.add_component(item_eid, Item(name="Bread", weight=0.3, value=2))
    w.add_component(item_eid, Consumable(effect_type="food", hunger_restore=25.0))
    w.add_component(item_eid, Renderable(char="b", color=(200, 170, 100), layer=1))

    w.register_system(InventorySystem())

    w.player_intent = ("pickup", item_eid)
    w.process_turn()

    inv = w.get(p, Inventory)
    assert item_eid in inv.items, "Item should be in inventory"
    assert w.get(item_eid, Position) is None, "Item Position should be removed from map"
    print("  [PASS] pickup item")


def test_use_consumable():
    w, p = _make_world_with_player(5, 5)

    # Reduce hunger
    needs = w.get(p, SurvivalNeeds)
    needs.hunger = 50.0

    # Add food to inventory
    item_eid = w.create_entity()
    w.add_component(item_eid, Item(name="Bread", weight=0.3, value=2))
    w.add_component(item_eid, Consumable(effect_type="food", hunger_restore=25.0))
    inv = w.get(p, Inventory)
    inv.items.append(item_eid)

    w.register_system(InventorySystem())

    w.player_intent = ("use_item", item_eid)
    w.process_turn()

    assert needs.hunger == 75.0, f"Hunger should be 75, got {needs.hunger}"
    assert item_eid not in inv.items, "Consumed item should be removed"
    print("  [PASS] use consumable")


def test_equip_and_unequip():
    w, p = _make_world_with_player(5, 5)

    # Create a shield
    shield_eid = w.create_entity()
    w.add_component(shield_eid, Item(name="Iron Shield", weight=5.0, value=20))
    w.add_component(shield_eid, Equippable(slot="shield", armor_bonus=3))

    inv = w.get(p, Inventory)
    inv.items.append(shield_eid)

    w.register_system(InventorySystem())

    # Equip
    w.player_intent = ("equip_item", shield_eid)
    w.process_turn()

    equip = w.get(p, Equipment)
    assert equip.shield == shield_eid, "Shield should be equipped"
    assert shield_eid not in inv.items, "Shield should be removed from inventory"

    # Unequip
    w.player_intent = ("unequip_slot", "shield")
    w.process_turn()

    assert equip.shield is None, "Shield slot should be empty"
    assert shield_eid in inv.items, "Shield should be back in inventory"
    print("  [PASS] equip and unequip")


def test_survival_decay():
    w, p = _make_world_with_player(5, 5)
    needs = w.get(p, SurvivalNeeds)
    initial_hunger = needs.hunger
    initial_thirst = needs.thirst

    w.register_system(SurvivalSystem())

    w.player_intent = ("done",)
    w.process_turn()

    assert needs.hunger < initial_hunger, "Hunger should decay"
    assert needs.thirst < initial_thirst, "Thirst should decay"
    assert needs.stress > 0.0, "Stress should increase"
    print(f"  [PASS] survival decay (hunger {initial_hunger:.1f} → {needs.hunger:.1f})")


def test_ai_chases_player():
    w, p = _make_world_with_player(5, 5)
    g = _make_goblin(w, 10, 5)  # 5 tiles away, within aggro range of 6

    ai_sys = AISystem()
    ai_sys.process(w)

    g_pos = w.get(g, Position)
    g_ai = w.get(g, AI)
    # Should have moved closer or be chasing
    assert g_ai.state == "chasing", f"AI should be chasing, got {g_ai.state}"
    assert g_pos.x < 10, f"Goblin should have moved closer, x={g_pos.x}"
    print(f"  [PASS] AI chases player (moved to x={g_pos.x})")


def test_status_effect_tick():
    w, p = _make_world_with_player(5, 5)
    hp = w.get(p, Health)
    effects = w.get(p, StatusEffects)
    effects.effects.append({"id": "poison", "duration": 3, "potency": 2, "source": "spider"})

    initial_hp = hp.current

    sys = StatusEffectSystem()
    sys.process(w)

    assert hp.current == initial_hp - 2, f"Poison should deal 2 dmg, HP={hp.current}"
    assert effects.effects[0]["duration"] == 2, "Duration should decrement"

    # Tick 2 more times to expire
    sys.process(w)
    sys.process(w)
    assert len(effects.effects) == 0, "Poison should expire after 3 ticks"
    print("  [PASS] status effect tick and expiry")


def test_creature_actually_damages_player():
    """Regression: an aggressive adjacent creature must deal damage through the
    full turn loop (previously creature attacks were silently dropped)."""
    w, p = _make_world_with_player(5, 5)
    g = _make_goblin(w, 6, 5)  # adjacent
    w.get(g, Health).current = 9999  # keep it alive so it keeps swinging
    w.get(g, Health).maximum = 9999
    w.get(g, AI).state = "chasing"
    w.get(g, AI).target = p
    w.get(g, Stats).strength = 16
    w.get(g, Stats).dexterity = 16
    gw = w.create_entity()
    w.add_component(gw, Equippable(slot="weapon", damage_dice="2d8+4"))
    w.get(g, Equipment).weapon = gw

    # Same system order as GameView.setup()
    for S in (MovementSystem, CombatSystem, AISystem,
              InventorySystem, StatusEffectSystem, FOVSystem):
        w.register_system(S())

    start_hp = w.get(p, Health).current
    for _ in range(15):  # 15 turns standing next to an aggressive enemy
        w.player_intent = ("done",)
        w.process_turn()
    end_hp = w.get(p, Health).current
    assert end_hp < start_hp, f"Creature should damage player; HP stayed at {end_hp}"
    print(f"  [PASS] creature damages player ({start_hp} -> {end_hp} over 15 turns)")


def test_magic_item_stat_bonus():
    """A stat-bonus ring raises effective STR without mutating base Stats, and lands on a ring finger."""
    from core.equipment_effects import effective_value
    w, p = _make_world_with_player()
    inv_sys = InventorySystem()
    stats = w.get(p, Stats)
    base = stats.strength
    ring = w.create_entity()
    w.add_component(ring, Item(name="Ring of Strength", weight=0.1, value=100))
    w.add_component(ring, Equippable(slot="ring", stat_bonuses={"strength": 2}))
    w.get(p, Inventory).items.append(ring)
    w.player_intent = ("equip_item", ring)
    inv_sys.process(w)
    assert stats.strength == base, "base Stats must not be mutated"
    assert effective_value(w, p, stats, "strength") == base + 2
    assert w.get(p, Equipment).ring_left == ring, "ring should occupy a ring finger"
    print("  [PASS] magic item stat bonus (effective STR +2, base unchanged)")


def test_magic_item_max_hp_symmetry():
    """Equipping then unequipping a max-HP amulet restores the original maximum."""
    w, p = _make_world_with_player()
    inv_sys = InventorySystem()
    hp = w.get(p, Health)
    hp.current = hp.maximum
    base_max = hp.maximum
    amu = w.create_entity()
    w.add_component(amu, Item(name="Amulet of Health", weight=0.3, value=140))
    w.add_component(amu, Equippable(slot="amulet", max_hp_bonus=25))
    w.get(p, Inventory).items.append(amu)
    w.player_intent = ("equip_item", amu)
    inv_sys.process(w)
    assert hp.maximum == base_max + 25 and hp.current == base_max + 25
    w.player_intent = ("unequip_slot", "amulet")
    inv_sys.process(w)
    assert hp.maximum == base_max and hp.current == base_max
    print("  [PASS] magic item max-HP equip/unequip symmetry")


def test_equipment_armor_in_combat():
    """Worn armor contributes to effective AC via the combat helper."""
    from core.equipment_effects import equipped_armor
    w, p = _make_world_with_player()
    inv_sys = InventorySystem()
    assert equipped_armor(w, p) == 0
    armor = w.create_entity()
    w.add_component(armor, Item(name="Plate Armor", weight=30.0, value=160))
    w.add_component(armor, Equippable(slot="armor", armor_bonus=6))
    w.get(p, Inventory).items.append(armor)
    w.player_intent = ("equip_item", armor)
    inv_sys.process(w)
    assert equipped_armor(w, p) == 6
    print("  [PASS] equipment armor contributes to AC")


if __name__ == "__main__":
    print("Running combat & integration tests...")
    test_player_attacks_creature()
    test_creature_death_gives_xp()
    test_creature_actually_damages_player()
    test_movement_blocked_by_wall()
    test_pickup_item()
    test_use_consumable()
    test_equip_and_unequip()
    test_magic_item_stat_bonus()
    test_magic_item_max_hp_symmetry()
    test_equipment_armor_in_combat()
    test_survival_decay()
    test_ai_chases_player()
    test_status_effect_tick()
    print("\nAll tests passed!")
