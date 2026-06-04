"""
SurvivalSystem — decays player needs each turn and applies consequences.
"""
from __future__ import annotations
from ecs.world import World
from ecs.component import (
    Player, SurvivalNeeds, Health, Mana, Stats, FieldOfView,
)
from core.equipment_effects import equipped_regen
from constants import (
    HUNGER_DECAY, THIRST_DECAY, SLEEP_DECAY,
    STRESS_PASSIVE_GAIN, WILLPOWER_DECAY,
    SURVIVAL_DANGER, SURVIVAL_CRITICAL,
    STRESS_DANGER, STRESS_CRITICAL,
    WILLPOWER_DANGER, WILLPOWER_CRITICAL,
)


class SurvivalSystem:
    def process(self, world: World) -> None:
        result = world.query_single(Player, SurvivalNeeds, Health, Mana)
        if result is None:
            return
        p_eid, _, needs, hp, mana = result

        # ── Decay ───────────────────────────────────
        needs.hunger = max(0.0, needs.hunger - HUNGER_DECAY)
        needs.thirst = max(0.0, needs.thirst - THIRST_DECAY)
        needs.sleep = max(0.0, needs.sleep - SLEEP_DECAY)
        needs.stress = min(100.0, needs.stress + STRESS_PASSIVE_GAIN)

        # Willpower decays faster when stressed
        wp_decay = WILLPOWER_DECAY
        if needs.stress >= STRESS_DANGER:
            wp_decay *= 2.0
        needs.willpower = max(0.0, needs.willpower - wp_decay)

        # ── Equipment regeneration (rings/talismans) ─
        regen = equipped_regen(world, p_eid)
        if regen and hp.alive and hp.current < hp.maximum:
            hp.current = min(hp.maximum, hp.current + regen)

        # ── Consequences (every 10 turns to avoid spam) ─
        if world.turn % 10 != 0:
            return

        # Hunger
        if needs.hunger <= SURVIVAL_CRITICAL:
            hp.current -= 1
            if hp.current <= 0:
                world.cause_of_death = "Starved to death"
            if world.turn % 50 == 0:
                world.log("You are starving! (-1 HP)", (200, 100, 40))
        elif needs.hunger <= SURVIVAL_DANGER:
            if world.turn % 50 == 0:
                world.log("You feel very hungry...", (180, 130, 40))

        # Thirst
        if needs.thirst <= SURVIVAL_CRITICAL:
            hp.current -= 2
            if hp.current <= 0:
                world.cause_of_death = "Died of dehydration"
            if world.turn % 50 == 0:
                world.log("You are severely dehydrated! (-2 HP)", (40, 150, 200))
        elif needs.thirst <= SURVIVAL_DANGER:
            if world.turn % 50 == 0:
                world.log("You are very thirsty...", (40, 150, 200))

        # Sleep
        if needs.sleep <= 5.0:
            if world.turn % 50 == 0:
                world.log("You can barely stay awake...", (120, 80, 180))
        elif needs.sleep <= 20.0:
            if world.turn % 50 == 0:
                world.log("You feel drowsy...", (120, 80, 180))

        # Stress
        if needs.stress >= STRESS_CRITICAL:
            if world.turn % 50 == 0:
                world.log("Panic overwhelms you!", (200, 100, 40))

        # Willpower
        if needs.willpower <= WILLPOWER_CRITICAL:
            if world.turn % 50 == 0:
                world.log("Your will is nearly broken...", (200, 200, 80))
