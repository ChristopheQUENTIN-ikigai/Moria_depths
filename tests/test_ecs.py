"""Tests for ECS core, dice, and map loading."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ecs.world import World
from ecs.component import Position, Renderable, Blocker, Health, Stats, Player
from core.dice import roll_dice, roll_d20


def test_entity_create_destroy():
    w = World()
    e1 = w.create_entity()
    e2 = w.create_entity()
    assert e1 != e2
    assert w.entity_exists(e1)
    w.destroy_entity(e1)
    assert not w.entity_exists(e1)
    assert w.entity_exists(e2)
    print("  [PASS] entity create/destroy")


def test_components():
    w = World()
    e = w.create_entity()
    w.add_component(e, Position(x=5, y=10, depth=1))
    w.add_component(e, Health(current=50, maximum=100))

    pos = w.get(e, Position)
    assert pos is not None
    assert pos.x == 5 and pos.y == 10

    hp = w.get(e, Health)
    assert hp.current == 50
    assert hp.ratio == 0.5

    w.remove_component(e, Health)
    assert w.get(e, Health) is None
    print("  [PASS] component add/get/remove")


def test_query():
    w = World()
    e1 = w.create_entity()
    w.add_component(e1, Position(x=0, y=0, depth=1))
    w.add_component(e1, Health(current=100, maximum=100))

    e2 = w.create_entity()
    w.add_component(e2, Position(x=1, y=1, depth=1))

    e3 = w.create_entity()
    w.add_component(e3, Position(x=2, y=2, depth=1))
    w.add_component(e3, Health(current=50, maximum=50))

    results = w.query(Position, Health)
    eids = [r[0] for r in results]
    assert e1 in eids
    assert e3 in eids
    assert e2 not in eids
    print("  [PASS] query multi-component")


def test_is_blocked():
    w = World()
    e = w.create_entity()
    w.add_component(e, Position(x=3, y=3, depth=1))
    w.add_component(e, Blocker(blocks_sight=True))

    assert w.is_blocked(3, 3, 1)
    assert not w.is_blocked(4, 4, 1)
    assert w.blocks_sight_at(3, 3, 1)
    print("  [PASS] is_blocked / blocks_sight_at")


def test_get_entities_at():
    w = World()
    e1 = w.create_entity()
    w.add_component(e1, Position(x=5, y=5, depth=1))
    e2 = w.create_entity()
    w.add_component(e2, Position(x=5, y=5, depth=1))
    e3 = w.create_entity()
    w.add_component(e3, Position(x=6, y=5, depth=1))

    at_5_5 = w.get_entities_at(5, 5, 1)
    assert e1 in at_5_5
    assert e2 in at_5_5
    assert e3 not in at_5_5
    print("  [PASS] get_entities_at")


def test_dice():
    for _ in range(100):
        r = roll_d20()
        assert 1 <= r <= 20

    for _ in range(100):
        r = roll_dice("2d6+3")
        assert 5 <= r <= 15  # 2*1+3=5, 2*6+3=15

    for _ in range(100):
        r = roll_dice("1d4")
        assert 1 <= r <= 4

    for _ in range(100):
        r = roll_dice("3d8-2")
        assert 1 <= r <= 22  # 3*1-2=1, 3*8-2=22

    print("  [PASS] dice rolls")


def test_stats_modifier():
    s = Stats(strength=16, dexterity=8, constitution=10)
    assert s.modifier("strength") == 3    # (16-10)//2
    assert s.modifier("dexterity") == -1   # (8-10)//2
    assert s.modifier("constitution") == 0 # (10-10)//2
    print("  [PASS] stats modifier")


def test_health_properties():
    h = Health(current=75, maximum=100)
    assert h.alive is True
    assert abs(h.ratio - 0.75) < 0.001

    h.current = 0
    assert h.alive is False
    assert h.ratio == 0.0
    print("  [PASS] health properties")


def test_message_log():
    w = World()
    w.log("Hello", (255, 255, 255))
    w.log("World", (200, 200, 200))
    assert len(w.messages) == 2
    assert w.messages[0][0] == "Hello"
    print("  [PASS] message log")


def test_map_loading():
    """Test that level_01.txt loads without errors."""
    w = World()
    map_path = os.path.join(os.path.dirname(__file__), "..", "assets", "maps", "level_01.txt")
    if os.path.exists(map_path):
        from core.map_loader import load_level
        width, height = load_level(w, map_path, 1)
        assert width > 0
        assert height > 0
        # Player should exist
        result = w.query_single(Player, Position)
        assert result is not None
        _, _, pos = result
        assert pos.depth == 1
        print(f"  [PASS] map loading ({width}x{height}, player at {pos.x},{pos.y})")
    else:
        print("  [SKIP] map loading (file not found)")


def test_spatial_index_consistency():
    w = World()

    def reference():
        r = {}
        for eid, comps in w._components.items():
            p = comps.get(Position)
            if p:
                r.setdefault((p.x, p.y, p.depth), set()).add(eid)
        return r

    def maintained():
        return {k: v for k, v in w._spatial.items() if v}

    e1 = w.create_entity(); w.add_component(e1, Position(1, 1, 1)); w.add_component(e1, Blocker())
    e2 = w.create_entity(); w.add_component(e2, Position(1, 1, 1))
    e3 = w.create_entity(); w.add_component(e3, Position(2, 2, 1))
    assert maintained() == reference()
    assert w.is_blocked(1, 1, 1) and not w.is_blocked(2, 2, 1)
    assert sorted(w.get_entities_at(1, 1, 1)) == sorted([e1, e2])

    w.move_entity(e1, 5, 5)                       # blocker leaves (1,1)
    assert maintained() == reference()
    assert not w.is_blocked(1, 1, 1) and w.is_blocked(5, 5, 1)

    w.move_entity(e3, 9, 9, 2)                     # change depth
    assert maintained() == reference()
    assert w.get_entities_at(9, 9, 2) == [e3]
    assert w.get_entities_at(2, 2, 1) == []

    w.remove_component(e2, Position)               # position removed
    assert maintained() == reference()
    w.destroy_entity(e1)                           # entity destroyed
    assert maintained() == reference()
    print("  [PASS] spatial index consistency (move/depth/remove/destroy)")


if __name__ == "__main__":
    print("Running tests...")
    test_entity_create_destroy()
    test_components()
    test_query()
    test_is_blocked()
    test_get_entities_at()
    test_spatial_index_consistency()
    test_dice()
    test_stats_modifier()
    test_health_properties()
    test_message_log()
    test_map_loading()
    print("\nAll tests passed!")
