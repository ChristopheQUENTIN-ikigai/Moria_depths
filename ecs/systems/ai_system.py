"""
AISystem — decides creature actions each turn.

Simple state machine:
  idle → chasing (if player in aggro range)
  chasing → attacking (if adjacent to player)
  chasing → fleeing (if HP critically low and behavior != boss)
"""
from __future__ import annotations
from ecs.world import World
from ecs.component import (
    Position, Player, AI, Health, Stats, Blocker, CreatureType,
)
from core.pathfinding import bresenham_distance, step_toward


class AISystem:
    """Processes all AI-tagged entities, moves them or queues attacks."""

    def process(self, world: World) -> None:
        player_result = world.query_single(Player, Position, Health)
        if not player_result:
            return
        p_eid, _, p_pos, p_hp = player_result

        if not p_hp.alive:
            return

        creature_attacks: list[tuple[int, int]] = []

        for eid, ai, c_pos, c_hp in world.query(AI, Position, Health):
            if not c_hp.alive:
                continue
            if c_pos.depth != world.current_depth:
                continue

            dist = bresenham_distance(c_pos.x, c_pos.y, p_pos.x, p_pos.y)

            # ── State transitions ───────────────────
            if ai.state == "idle":
                if dist <= ai.aggro_range:
                    ai.state = "chasing"
                    ai.target = p_eid

            if ai.state == "chasing":
                if dist > ai.aggro_range * 2:
                    ai.state = "idle"
                    ai.target = None
                elif c_hp.current < c_hp.maximum * 0.2 and ai.behavior != "boss":
                    ai.state = "fleeing"

            if ai.state == "fleeing":
                if c_hp.current > c_hp.maximum * 0.4:
                    ai.state = "chasing"

            # ── Actions ─────────────────────────────
            if ai.state == "chasing":
                if dist <= 1:
                    # Adjacent → attack
                    creature_attacks.append((eid, p_eid))
                else:
                    # Move toward player
                    nx, ny = step_toward(
                        c_pos.x, c_pos.y, p_pos.x, p_pos.y
                    )
                    if not world.is_blocked(nx, ny, c_pos.depth):
                        # Also don't step on other creatures
                        occupied = False
                        for other_eid in world.get_entities_at(nx, ny, c_pos.depth):
                            if other_eid != eid and world.has(other_eid, AI):
                                occupied = True
                                break
                        if not occupied:
                            world.move_entity(eid, nx, ny)

            elif ai.state == "fleeing":
                # Move away from player
                nx, ny = step_toward(
                    c_pos.x, c_pos.y, p_pos.x, p_pos.y, away=True
                )
                if not world.is_blocked(nx, ny, c_pos.depth):
                    world.move_entity(eid, nx, ny)

        # Resolve creature attacks NOW. (Previously these were written to
        # world.player_intent, but the combat system had already run for this
        # turn and process_turn() clears the intent afterwards — so enemies
        # never actually dealt any damage.)
        if creature_attacks:
            from ecs.systems.combat_system import CombatSystem
            combat = CombatSystem()
            for attacker_eid, defender_eid in creature_attacks:
                combat._creature_attack(world, attacker_eid, defender_eid)
