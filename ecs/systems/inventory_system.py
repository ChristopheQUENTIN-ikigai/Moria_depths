"""
InventorySystem — handles item pick-up, use, equip, unequip, drop.
"""
from __future__ import annotations
from ecs.world import World
from ecs.component import (
    Position, Player, Inventory, Equipment, Item, Consumable,
    Equippable, SpellSource, Health, Mana, SurvivalNeeds,
    SpellKnowledge, Renderable, StatusEffects,
)


class InventorySystem:
    def process(self, world: World) -> None:
        intent = world.player_intent
        if not intent:
            return

        if intent[0] == "pickup":
            self._pickup(world, intent[1])
            world.player_intent = ("done",)

        elif intent[0] == "use_item":
            self._use_item(world, intent[1])
            world.player_intent = ("done",)

        elif intent[0] == "equip_item":
            self._equip_item(world, intent[1])
            world.player_intent = ("done",)

        elif intent[0] == "unequip_slot":
            self._unequip_slot(world, intent[1])
            world.player_intent = ("done",)

        elif intent[0] == "drop_item":
            self._drop_item(world, intent[1])
            world.player_intent = ("done",)

    # ── Equip-effect deltas (max HP / max mana) ─────

    def _apply_equip_effects(self, world: World, p_eid: int, item_eid: int, sign: int) -> None:
        """Apply (sign=+1) or revert (sign=-1) an item's max-HP/mana bonuses."""
        eq = world.get(item_eid, Equippable)
        if not eq:
            return
        hp = world.get(p_eid, Health)
        mana = world.get(p_eid, Mana)
        if hp and eq.max_hp_bonus:
            hp.maximum = max(1, hp.maximum + sign * eq.max_hp_bonus)
            if sign > 0:
                hp.current += eq.max_hp_bonus
            hp.current = min(hp.current, hp.maximum)
        if mana and eq.max_mana_bonus:
            mana.maximum = max(0, mana.maximum + sign * eq.max_mana_bonus)
            if sign > 0:
                mana.current += eq.max_mana_bonus
            mana.current = min(mana.current, mana.maximum)

    # ── Pick up ─────────────────────────────────────

    def _pickup(self, world: World, item_eid: int) -> None:
        player = world.query_single(Player, Inventory, Position)
        if not player:
            return
        p_eid, _, inv, p_pos = player

        item = world.get(item_eid, Item)
        if not item:
            return

        if len(inv.items) >= inv.max_slots:
            world.log("Inventory is full!", (200, 100, 100))
            return

        inv.items.append(item_eid)
        # Remove from map (remove Position so it's no longer rendered on map)
        world.remove_component(item_eid, Position)
        world.log(f"Picked up {item.name}.", (255, 215, 0))

    # ── Use consumable ──────────────────────────────

    def _use_item(self, world: World, item_eid: int) -> None:
        player = world.query_single(Player, Inventory, Health, Mana, SurvivalNeeds)
        if not player:
            return
        p_eid, _, inv, hp, mana, needs = player

        if item_eid not in inv.items:
            return

        cons = world.get(item_eid, Consumable)
        spell_src = world.get(item_eid, SpellSource)
        item = world.get(item_eid, Item)
        item_name = item.name if item else "item"

        if cons:
            # Apply consumable effects
            if cons.hp_restore:
                hp.current = min(hp.maximum, hp.current + cons.hp_restore)
                world.log(f"Restored {cons.hp_restore} HP.", (100, 255, 100))
            if cons.mana_restore:
                mana.current = min(mana.maximum, mana.current + cons.mana_restore)
                world.log(f"Restored {cons.mana_restore} mana.", (100, 100, 255))
            if cons.hunger_restore:
                needs.hunger = min(100.0, needs.hunger + cons.hunger_restore)
            if cons.thirst_restore:
                needs.thirst = min(100.0, needs.thirst + cons.thirst_restore)
            if cons.sleep_restore:
                needs.sleep = min(100.0, needs.sleep + cons.sleep_restore)
            if cons.stress_reduce:
                needs.stress = max(0.0, needs.stress - cons.stress_reduce)
            if cons.willpower_restore:
                needs.willpower = min(100.0, needs.willpower + cons.willpower_restore)

            if cons.effect_type == "cure":
                se = world.get(p_eid, StatusEffects)
                removed = 0
                if se:
                    before = len(se.effects)
                    se.effects[:] = [e for e in se.effects
                                     if e.get("id") not in ("poison", "bleed")]
                    removed = before - len(se.effects)
                if removed:
                    world.log("The antidote purges the toxins from your body.", (120, 220, 120))
                else:
                    world.log("You feel fine; there's nothing to cure.", (180, 180, 180))

            world.log(f"Used {item_name}.", (200, 200, 150))
            inv.items.remove(item_eid)
            world.destroy_entity(item_eid)

        elif spell_src:
            if spell_src.source_type == "book":
                # Learn spell permanently
                sk = world.get(p_eid, SpellKnowledge)
                if sk is None:
                    sk = SpellKnowledge()
                    world.add_component(p_eid, sk)
                if spell_src.spell_id not in sk.known_spells:
                    sk.known_spells.append(spell_src.spell_id)
                    world.log(
                        f"Learned spell: {spell_src.spell_id}!",
                        (180, 120, 255),
                    )
                else:
                    world.log("You already know this spell.", (180, 180, 180))
                    return
                inv.items.remove(item_eid)
                world.destroy_entity(item_eid)
            elif spell_src.source_type == "parchment":
                # Instant cast — will be handled by magic system
                world.log(
                    f"Cast {spell_src.spell_id} from parchment!",
                    (180, 120, 255),
                )
                spell_src.charges -= 1
                if spell_src.charges <= 0:
                    inv.items.remove(item_eid)
                    world.destroy_entity(item_eid)
        else:
            world.log(f"Can't use {item_name}.", (180, 180, 180))

    # ── Equip ───────────────────────────────────────

    def _equip_item(self, world: World, item_eid: int) -> None:
        player = world.query_single(Player, Inventory, Equipment)
        if not player:
            return
        p_eid, _, inv, equip = player

        if item_eid not in inv.items:
            return

        eq = world.get(item_eid, Equippable)
        item = world.get(item_eid, Item)
        if not eq:
            world.log("This item cannot be equipped.", (180, 180, 180))
            return

        slot = eq.slot
        # "ring" is a pseudo-slot: route to whichever ring finger is free.
        if slot == "ring":
            if equip.ring_left is None:
                slot = "ring_left"
            elif equip.ring_right is None:
                slot = "ring_right"
            else:
                slot = "ring_left"  # both occupied → replace the left one
        if not hasattr(equip, slot):
            world.log(f"No equipment slot: {slot}.", (200, 100, 100))
            return

        # Unequip current item in that slot first
        current = getattr(equip, slot)
        if current is not None:
            inv.items.append(current)
            self._apply_equip_effects(world, p_eid, current, -1)
            cur_item = world.get(current, Item)
            if cur_item:
                world.log(f"Unequipped {cur_item.name}.", (180, 180, 150))

        setattr(equip, slot, item_eid)
        inv.items.remove(item_eid)
        self._apply_equip_effects(world, p_eid, item_eid, +1)
        world.log(f"Equipped {item.name if item else 'item'}.", (150, 200, 255))

    # ── Unequip ─────────────────────────────────────

    def _unequip_slot(self, world: World, slot: str) -> None:
        player = world.query_single(Player, Inventory, Equipment)
        if not player:
            return
        p_eid, _, inv, equip = player

        current = getattr(equip, slot, None)
        if current is None:
            world.log(f"Nothing equipped in {slot}.", (180, 180, 180))
            return

        if len(inv.items) >= inv.max_slots:
            world.log("Inventory is full, can't unequip!", (200, 100, 100))
            return

        inv.items.append(current)
        setattr(equip, slot, None)
        self._apply_equip_effects(world, p_eid, current, -1)
        item = world.get(current, Item)
        world.log(f"Unequipped {item.name if item else 'item'}.", (180, 180, 150))

    # ── Drop ────────────────────────────────────────

    def _drop_item(self, world: World, item_eid: int) -> None:
        player = world.query_single(Player, Inventory, Position)
        if not player:
            return
        p_eid, _, inv, p_pos = player

        if item_eid not in inv.items:
            return

        inv.items.remove(item_eid)
        # Place back on map at player position
        world.add_component(item_eid, Position(x=p_pos.x, y=p_pos.y, depth=p_pos.depth))
        item = world.get(item_eid, Item)
        world.log(f"Dropped {item.name if item else 'item'}.", (180, 180, 150))
