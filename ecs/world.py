"""
World — the ECS registry.

Stores all entities and their components.  Runs systems each turn.
"""
from __future__ import annotations
from typing import Any, Protocol, Sequence

from ecs.entity import Entity
from ecs.component import Position, Blocker


class System(Protocol):
    """Any object with a process(world) method can be a system."""
    def process(self, world: "World") -> None: ...


class World:
    """Central ECS registry — entities, components, and systems."""

    def __init__(self) -> None:
        self._next_id: int = 0
        # eid → {ComponentType: component_instance}
        self._components: dict[int, dict[type, Any]] = {}
        self._systems: list[System] = []

        # Per-turn intent set by input handler, consumed by systems
        self.player_intent: tuple | None = None

        # Message log — list of (text, color) tuples
        self.messages: list[tuple[str, tuple]] = []

        # Current dungeon depth the player is on
        self.current_depth: int = 1

        # Turn counter
        self.turn: int = 0

        # Cause of death — set by combat/survival systems
        self.cause_of_death: str = "Unknown"

        # Spatial index: (x, y, depth) → set of entity ids with a Position there.
        # Keeps tile lookups (is_blocked / get_entities_at / FOV) O(1).
        self._spatial: dict[tuple[int, int, int], set[int]] = {}

        # Cached player entity id for O(1) per-frame lookups.
        self.player_eid: int | None = None

    # ── Spatial index helpers ──────────────────────────

    def _index_add(self, eid: int, pos: Position) -> None:
        self._spatial.setdefault((pos.x, pos.y, pos.depth), set()).add(eid)

    def _index_remove(self, eid: int, pos: Position) -> None:
        key = (pos.x, pos.y, pos.depth)
        bucket = self._spatial.get(key)
        if bucket is not None:
            bucket.discard(eid)
            if not bucket:
                del self._spatial[key]

    def move_entity(self, eid: int, x: int, y: int, depth: int | None = None) -> None:
        """Move an entity to a new tile, keeping the spatial index in sync.
        ALL position changes must go through this (never mutate pos.x/y directly)."""
        pos = self.get(eid, Position)
        if pos is None:
            return
        self._index_remove(eid, pos)
        pos.x, pos.y = x, y
        if depth is not None:
            pos.depth = depth
        self._index_add(eid, pos)

    # ── Entity management ──────────────────────────────

    def create_entity(self) -> int:
        eid = self._next_id
        self._next_id += 1
        self._components[eid] = {}
        return eid

    def destroy_entity(self, eid: int) -> None:
        comps = self._components.get(eid)
        if comps is not None:
            pos = comps.get(Position)
            if pos is not None:
                self._index_remove(eid, pos)
        self._components.pop(eid, None)
        if self.player_eid == eid:
            self.player_eid = None

    def entity_exists(self, eid: int) -> bool:
        return eid in self._components

    # ── Component management ───────────────────────────

    def add_component(self, eid: int, component: Any) -> None:
        if eid not in self._components:
            raise KeyError(f"Entity {eid} does not exist")
        if isinstance(component, Position):
            old = self._components[eid].get(Position)
            if old is not None:
                self._index_remove(eid, old)
            self._index_add(eid, component)
        self._components[eid][type(component)] = component

    def remove_component(self, eid: int, comp_type: type) -> None:
        comps = self._components.get(eid)
        if comps is None:
            return
        if comp_type is Position:
            pos = comps.get(Position)
            if pos is not None:
                self._index_remove(eid, pos)
        comps.pop(comp_type, None)

    def get(self, eid: int, comp_type: type) -> Any | None:
        return self._components.get(eid, {}).get(comp_type)

    def has(self, eid: int, *comp_types: type) -> bool:
        comps = self._components.get(eid, {})
        return all(ct in comps for ct in comp_types)

    # ── Queries ────────────────────────────────────────

    def query(self, *comp_types: type) -> list[tuple]:
        """Return [(eid, comp1, comp2, ...) for entities having ALL listed component types]."""
        results = []
        for eid, comps in self._components.items():
            if all(ct in comps for ct in comp_types):
                results.append(
                    (eid, *(comps[ct] for ct in comp_types))
                )
        return results

    def query_single(self, *comp_types: type) -> tuple | None:
        """Like query() but returns the first match or None."""
        for eid, comps in self._components.items():
            if all(ct in comps for ct in comp_types):
                return (eid, *(comps[ct] for ct in comp_types))
        return None

    def player(self, *comp_types: type) -> tuple | None:
        """Fast player lookup using the cached eid (falls back to a scan).
        Pass the components you need, e.g. world.player(Player, Health)."""
        eid = self.player_eid
        if eid is not None:
            comps = self._components.get(eid)
            if comps is not None and all(ct in comps for ct in comp_types):
                return (eid, *(comps[ct] for ct in comp_types))
        result = self.query_single(*comp_types)
        if result is not None:
            self.player_eid = result[0]
        return result

    def get_entities_at(self, x: int, y: int, depth: int) -> list[int]:
        """Return entity IDs at a specific tile position (O(1) via index)."""
        return list(self._spatial.get((x, y, depth), ()))

    def is_blocked(self, x: int, y: int, depth: int) -> bool:
        """Check if a tile is blocked by any Blocker entity (O(1) via index)."""
        for eid in self._spatial.get((x, y, depth), ()):
            if Blocker in self._components.get(eid, {}):
                return True
        return False

    def blocks_sight_at(self, x: int, y: int, depth: int) -> bool:
        """Check if any entity at this tile blocks line of sight (O(1) via index)."""
        for eid in self._spatial.get((x, y, depth), ()):
            blk = self._components.get(eid, {}).get(Blocker)
            if blk is not None and blk.blocks_sight:
                return True
        return False

    # ── System management ──────────────────────────────

    def register_system(self, system: System) -> None:
        self._systems.append(system)

    def process_turn(self) -> None:
        """Execute all registered systems in order, then increment turn."""
        for system in self._systems:
            system.process(self)
        self.player_intent = None
        self.turn += 1

    # ── Messages ───────────────────────────────────────

    def log(self, text: str, color: tuple = (200, 200, 200)) -> None:
        from constants import MAX_LOG_MESSAGES
        self.messages.append((text, color))
        if len(self.messages) > MAX_LOG_MESSAGES:
            self.messages.pop(0)
