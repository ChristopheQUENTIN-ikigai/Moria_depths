"""
StatusEffectSystem — ticks active buffs/debuffs, applies damage/healing,
and expires effects when duration reaches 0.
"""
from __future__ import annotations
from ecs.world import World
from ecs.component import Health, StatusEffects


class StatusEffectSystem:
    def process(self, world: World) -> None:
        for eid, effects, hp in world.query(StatusEffects, Health):
            expired = []
            for i, eff in enumerate(effects.effects):
                eid_name = eff.get("id", "unknown")
                potency = eff.get("potency", 0)
                duration = eff.get("duration", 0)

                # Apply per-turn effect
                if eid_name == "poison":
                    hp.current -= potency
                elif eid_name == "regen":
                    hp.current = min(hp.maximum, hp.current + potency)
                elif eid_name == "bleed":
                    hp.current -= potency

                # Decrement duration
                eff["duration"] = duration - 1
                if eff["duration"] <= 0:
                    expired.append(i)

            # Remove expired (reverse to preserve indices)
            for i in reversed(expired):
                eff = effects.effects.pop(i)
                world.log(
                    f"Effect '{eff['id']}' has worn off.",
                    (180, 180, 180),
                )
