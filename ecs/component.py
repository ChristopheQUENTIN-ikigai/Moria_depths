"""
All ECS components — pure data, no logic.
"""
from __future__ import annotations
from dataclasses import dataclass, field


# ── Spatial / rendering ─────────────────────────────────

@dataclass
class Position:
    x: int = 0
    y: int = 0
    depth: int = 1

@dataclass
class Renderable:
    char: str = "?"
    color: tuple = (255, 255, 255)
    texture_path: str = ""
    layer: int = 0

@dataclass
class Blocker:
    blocks_sight: bool = False

# ── Player tag ──────────────────────────────────────────

@dataclass
class Player:
    name: str = "Adventurer"

# ── Core stats ──────────────────────────────────────────

@dataclass
class Stats:
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 8
    def modifier(self, attr: str) -> int:
        return (getattr(self, attr) - 10) // 2

@dataclass
class Health:
    current: int = 100
    maximum: int = 100
    @property
    def ratio(self) -> float:
        return max(0.0, self.current / self.maximum) if self.maximum else 0.0
    @property
    def alive(self) -> bool:
        return self.current > 0

@dataclass
class Mana:
    current: int = 50
    maximum: int = 50
    @property
    def ratio(self) -> float:
        return max(0.0, self.current / self.maximum) if self.maximum else 0.0

@dataclass
class SurvivalNeeds:
    hunger: float = 100.0
    thirst: float = 100.0
    sleep: float = 100.0
    stress: float = 0.0
    willpower: float = 100.0

@dataclass
class Experience:
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100
    xp_reward: int = 0

@dataclass
class FieldOfView:
    radius: int = 8
    visible_tiles: set = field(default_factory=set)
    explored_tiles: set = field(default_factory=set)

# ── Inventory / equipment ───────────────────────────────

@dataclass
class Inventory:
    items: list[int] = field(default_factory=list)
    max_slots: int = 20

@dataclass
class GoldPouch:
    amount: int = 0

@dataclass
class Gold:
    amount: int = 1

@dataclass
class Equipment:
    weapon: int | None = None
    armor: int | None = None
    helmet: int | None = None
    shield: int | None = None
    gloves: int | None = None
    boots: int | None = None
    amulet: int | None = None
    ring_left: int | None = None
    ring_right: int | None = None
    talisman: int | None = None
    def slot_names(self) -> list[str]:
        return ["weapon","armor","helmet","shield","gloves",
                "boots","amulet","ring_left","ring_right","talisman"]
    def get_all_equipped(self) -> list[int]:
        return [getattr(self, s) for s in self.slot_names() if getattr(self, s) is not None]

# ── Item components ─────────────────────────────────────

@dataclass
class Item:
    name: str = ""
    description: str = ""
    weight: float = 0.1
    value: int = 0

@dataclass
class Consumable:
    effect_type: str = ""
    potency: int = 0
    hunger_restore: float = 0.0
    thirst_restore: float = 0.0
    sleep_restore: float = 0.0
    stress_reduce: float = 0.0
    willpower_restore: float = 0.0
    hp_restore: int = 0
    mana_restore: int = 0

@dataclass
class Equippable:
    slot: str = ""
    armor_bonus: int = 0
    damage_dice: str = ""
    damage_type: str = "physical"
    stat_bonuses: dict = field(default_factory=dict)
    special: str = ""
    ranged: bool = False          # True for bows / crossbows
    ammo_type: str = ""           # "arrow" or "bolt" — required ammo
    max_hp_bonus: int = 0         # added to max HP while equipped
    max_mana_bonus: int = 0       # added to max mana while equipped
    regen: int = 0                # HP regenerated per turn while equipped

@dataclass
class Ammo:
    """Stackable ammunition."""
    ammo_type: str = "arrow"      # "arrow", "bolt"
    quantity: int = 10

@dataclass
class KeyItem:
    """A colored key that opens matching locked doors."""
    color: str = "red"            # "red","blue","green","yellow","purple"

@dataclass
class SpellSource:
    spell_id: str = ""
    source_type: str = "parchment"
    charges: int = 1

# ── Creature / AI ───────────────────────────────────────

@dataclass
class AI:
    behavior: str = "aggressive"
    aggro_range: int = 6
    state: str = "idle"
    target: int | None = None

@dataclass
class CreatureType:
    species: str = "goblin"
    xp_reward: int = 10

@dataclass
class LootTable:
    table_id: str = ""

# ── Status effects ──────────────────────────────────────

@dataclass
class StatusEffects:
    effects: list[dict] = field(default_factory=list)

# ── Spell knowledge ─────────────────────────────────────

@dataclass
class SpellKnowledge:
    known_spells: list[str] = field(default_factory=list)

# ── Map features ────────────────────────────────────────

@dataclass
class Door:
    is_open: bool = False
    locked: bool = False
    key_color: str = ""           # "" = unlocked, "red"/"blue"/... = needs key

@dataclass
class StairsDown:
    target_depth: int = 0

@dataclass
class StairsUp:
    target_depth: int = 0

@dataclass
class Trap:
    trap_type: str = "spike"
    damage: int = 10
    revealed: bool = False

@dataclass
class Chest:
    loot_table_id: str = "common_chest"
    opened: bool = False

@dataclass
class Fountain:
    uses_left: int = 3
    effect: str = "restore_thirst"

@dataclass
class Altar:
    used_this_visit: bool = False
