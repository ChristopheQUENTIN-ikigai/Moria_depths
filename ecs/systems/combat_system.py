"""
CombatSystem — resolves melee and ranged attacks.

Ranged: player_intent = ("ranged_attack", dx, dy)
  - Checks equipped weapon is ranged (bow/crossbow)
  - Checks matching ammo in inventory
  - Fires projectile along direction until hitting enemy or wall
"""
from __future__ import annotations
import random
from ecs.world import World
from ecs.component import (
    Position, Player, Health, Stats, Equipment, Equippable,
    AI, CreatureType, Experience, Blocker, Inventory, Ammo, Item,
)
from core.dice import roll_dice, roll_d20
from core.equipment_effects import effective_modifier, equipped_armor
from constants import BASE_AC, CRIT_ROLL, FUMBLE_ROLL, MAX_RANGED_RANGE


class CombatSystem:
    def process(self, world: World) -> None:
        intent = world.player_intent
        if not intent:
            return

        if intent[0] == "attack":
            self._player_melee(world, intent[1])
            world.player_intent = ("done",)

        elif intent[0] == "ranged_attack":
            self._player_ranged(world, intent[1], intent[2])
            world.player_intent = ("done",)

        elif intent[0] == "creature_attacks":
            for (attacker_eid, defender_eid) in intent[1]:
                self._creature_attack(world, attacker_eid, defender_eid)

    # ── Player melee ────────────────────────────────

    def _player_melee(self, world, target_eid):
        pr = world.query_single(Player, Stats, Health, Equipment)
        if not pr:
            return
        p_eid, _, p_stats, p_hp, p_equip = pr
        t_hp = world.get(target_eid, Health)
        t_stats = world.get(target_eid, Stats)
        t_equip = world.get(target_eid, Equipment)
        ctype = world.get(target_eid, CreatureType)
        name = ctype.species.title() if ctype else "creature"
        if not t_hp or not t_hp.alive:
            return
        self._resolve(world, p_eid, target_eid, p_stats, p_equip, t_stats, t_equip, t_hp, "You", name)
        self._check_death(world, target_eid, name, False)

    # ── Player ranged ───────────────────────────────

    def _player_ranged(self, world, dx, dy):
        pr = world.query_single(Player, Stats, Health, Equipment, Inventory, Position)
        if not pr:
            return
        p_eid, _, p_stats, p_hp, p_equip, inv, p_pos = pr

        # Check weapon is ranged
        if p_equip.weapon is None:
            world.log("No weapon equipped.", (180, 180, 180))
            return
        weap = world.get(p_equip.weapon, Equippable)
        if not weap or not weap.ranged:
            world.log("Your weapon is not ranged. Use melee (bump).", (180, 180, 180))
            return

        # Check ammo
        ammo_eid = self._find_ammo(world, inv, weap.ammo_type)
        if ammo_eid is None:
            world.log(f"No {weap.ammo_type}s left!", (200, 100, 100))
            return

        # Consume 1 ammo
        ammo_comp = world.get(ammo_eid, Ammo)
        ammo_comp.quantity -= 1
        if ammo_comp.quantity <= 0:
            inv.items.remove(ammo_eid)
            world.destroy_entity(ammo_eid)

        # Trace projectile
        cx, cy = p_pos.x, p_pos.y
        hit_eid = None
        for step in range(1, MAX_RANGED_RANGE + 1):
            cx += dx
            cy += dy
            if world.is_blocked(cx, cy, p_pos.depth):
                world.log("Your shot hits a wall.", (150, 150, 150))
                break
            for eid in world.get_entities_at(cx, cy, p_pos.depth):
                if world.has(eid, AI, Health):
                    hit_eid = eid
                    break
            if hit_eid:
                break
        else:
            world.log("Your shot disappears into the darkness.", (150, 150, 150))
            return

        if hit_eid is None:
            return

        t_hp = world.get(hit_eid, Health)
        t_stats = world.get(hit_eid, Stats)
        t_equip = world.get(hit_eid, Equipment)
        ctype = world.get(hit_eid, CreatureType)
        name = ctype.species.title() if ctype else "creature"
        if not t_hp or not t_hp.alive:
            return
        self._resolve(world, p_eid, hit_eid, p_stats, p_equip, t_stats, t_equip, t_hp, "You", name, ranged=True)
        self._check_death(world, hit_eid, name, False)

    def _find_ammo(self, world, inv, ammo_type):
        for eid in inv.items:
            a = world.get(eid, Ammo)
            if a and a.ammo_type == ammo_type:
                return eid
        return None

    # ── Creature attacks ────────────────────────────

    def _creature_attack(self, world, attacker_eid, defender_eid):
        a_stats = world.get(attacker_eid, Stats)
        a_equip = world.get(attacker_eid, Equipment)
        a_hp = world.get(attacker_eid, Health)
        ctype = world.get(attacker_eid, CreatureType)
        a_name = ctype.species.title() if ctype else "Creature"
        d_hp = world.get(defender_eid, Health)
        d_stats = world.get(defender_eid, Stats)
        d_equip = world.get(defender_eid, Equipment)
        if not a_hp or not a_hp.alive or not d_hp or not d_hp.alive:
            return
        self._resolve(world, attacker_eid, defender_eid, a_stats, a_equip, d_stats, d_equip, d_hp, a_name, "you")
        self._check_death(world, defender_eid, "you", True)

    # ── Resolution ──────────────────────────────────

    def _resolve(self, world, a_eid, d_eid, a_stats, a_equip, d_stats, d_equip, d_hp,
                 a_name, d_name, ranged=False):
        str_mod = effective_modifier(world, a_eid, a_stats, "strength")
        dex_mod_a = effective_modifier(world, a_eid, a_stats, "dexterity")
        weapon_dice = "1d4"
        if a_equip and a_equip.weapon is not None:
            weap = world.get(a_equip.weapon, Equippable)
            if weap and weap.damage_dice:
                weapon_dice = weap.damage_dice
        dex_mod_d = effective_modifier(world, d_eid, d_stats, "dexterity")
        armor_total = equipped_armor(world, d_eid)
        target_ac = BASE_AC + armor_total + dex_mod_d
        nat = roll_d20()
        # Melee attacks are governed by Strength, ranged by Dexterity.
        attack_mod = dex_mod_a if ranged else str_mod
        attack_roll = nat + attack_mod

        if nat == FUMBLE_ROLL:
            world.log(f"{a_name} fumble! Miss!", (180, 180, 60))
            return
        is_crit = nat == CRIT_ROLL
        if not is_crit and attack_roll < target_ac:
            world.log(f"{a_name} {'shoot' if ranged else 'attack'} {d_name} but miss.", (180, 180, 180))
            return
        base_dmg = roll_dice(weapon_dice)
        if is_crit:
            base_dmg += roll_dice(weapon_dice)
        total = base_dmg + (str_mod if not ranged else dex_mod_a)
        reduction = armor_total // 3
        final = max(1, total - reduction)
        d_hp.current -= final
        crit_str = " CRITICAL!" if is_crit else ""
        kind = "shoot" if ranged else "hit"
        color = (255, 100, 100) if d_name == "you" else (100, 255, 100)
        world.log(f"{a_name} {kind} {d_name} for {final} damage!{crit_str}", color)

    def _check_death(self, world, eid, name, is_player):
        hp = world.get(eid, Health)
        if not hp or hp.alive:
            return
        if is_player:
            world.log("You have been slain!", (255, 0, 0))
        else:
            world.log(f"{name} is slain!", (200, 200, 60))
            ctype = world.get(eid, CreatureType)
            if ctype:
                pr = world.query_single(Player, Experience)
                if pr:
                    _, _, p_xp = pr
                    p_xp.xp += ctype.xp_reward
                    world.log(f"+{ctype.xp_reward} XP", (80, 200, 80))
                    while p_xp.xp >= p_xp.xp_to_next:
                        p_xp.xp -= p_xp.xp_to_next
                        p_xp.level += 1
                        from constants import XP_BASE, XP_FACTOR
                        p_xp.xp_to_next = int(XP_BASE * (XP_FACTOR ** (p_xp.level - 1)))
                        world.log(f"*** LEVEL UP! Level {p_xp.level}! ***", (255, 255, 100))
                        # Boost HP on level up
                        p_hp_r = world.query_single(Player, Health)
                        if p_hp_r:
                            _, _, p_hp = p_hp_r
                            p_hp.maximum += 10
                            p_hp.current = min(p_hp.current + 10, p_hp.maximum)
            # Drop gold
            from core.map_loader import spawn_creature_loot_gold
            c_pos = world.get(eid, Position)
            if c_pos and ctype:
                spawn_creature_loot_gold(world, c_pos.x, c_pos.y, c_pos.depth, ctype.species)
            # Clean up the creature's owned equipment entities to avoid leaks.
            c_equip = world.get(eid, Equipment)
            if c_equip:
                for owned in c_equip.get_all_equipped():
                    world.destroy_entity(owned)
            world.destroy_entity(eid)
