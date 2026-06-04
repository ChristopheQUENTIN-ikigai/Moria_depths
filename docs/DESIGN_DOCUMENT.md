# Depths of Moria — Roguelike Dungeon Crawler

## Game Design Document & Technical Plan

**Engine:** Python 3.11 + Arcade 3.0.x  
**Genre:** Turn-based roguelike dungeon crawler  
**Theme:** Tolkien's Moria / Lord of the Rings bestiary  
**Architecture:** Entity Component System (ECS)

---

## 1. Project Folder Tree

```
moria_depths/
│
├── main.py                          # Entry point — creates arcade.Window, launches GameEngine
├── constants.py                     # Tile size, screen dims, colors, enums, key bindings
├── game_engine.py                   # Top-level controller: view switching, save/load dispatcher
│
├── assets/
│   ├── textures/
│   │   ├── player/
│   │   │   ├── warrior_idle.png
│   │   │   ├── mage_idle.png
│   │   │   └── ranger_idle.png
│   │   ├── creatures/
│   │   │   ├── goblin.png
│   │   │   ├── orc.png
│   │   │   ├── troll.png
│   │   │   ├── warg.png
│   │   │   ├── cave_spider.png
│   │   │   ├── balrog.png
│   │   │   ├── uruk_hai.png
│   │   │   ├── barrow_wight.png
│   │   │   ├── nazgul_shadow.png
│   │   │   └── dragon_worm.png
│   │   ├── tiles/
│   │   │   ├── floor_stone.png
│   │   │   ├── wall_stone.png
│   │   │   ├── wall_mossy.png
│   │   │   ├── door_closed.png
│   │   │   ├── door_open.png
│   │   │   ├── stairs_down.png
│   │   │   ├── stairs_up.png
│   │   │   ├── trap_hidden.png
│   │   │   ├── trap_revealed.png
│   │   │   ├── chest.png
│   │   │   ├── fountain.png
│   │   │   └── altar.png
│   │   ├── items/
│   │   │   ├── weapons/
│   │   │   │   ├── sword.png
│   │   │   │   ├── axe.png
│   │   │   │   ├── bow.png
│   │   │   │   ├── staff.png
│   │   │   │   ├── dagger.png
│   │   │   │   └── mace.png
│   │   │   ├── armor/
│   │   │   │   ├── leather_armor.png
│   │   │   │   ├── chainmail.png
│   │   │   │   ├── plate_armor.png
│   │   │   │   ├── helmet.png
│   │   │   │   ├── shield.png
│   │   │   │   ├── gloves.png
│   │   │   │   └── boots.png
│   │   │   ├── consumables/
│   │   │   │   ├── bread.png
│   │   │   │   ├── meat.png
│   │   │   │   ├── lembas.png
│   │   │   │   ├── water_flask.png
│   │   │   │   ├── ale.png
│   │   │   │   ├── miruvor.png
│   │   │   │   └── ent_draught.png
│   │   │   ├── magic/
│   │   │   │   ├── spell_parchment.png
│   │   │   │   ├── spell_book.png
│   │   │   │   ├── amulet.png
│   │   │   │   ├── talisman.png
│   │   │   │   └── ring.png
│   │   │   └── misc/
│   │   │       ├── torch.png
│   │   │       ├── key.png
│   │   │       └── gold.png
│   │   └── ui/
│   │       ├── heart.png
│   │       ├── mana_orb.png
│   │       ├── hunger_icon.png
│   │       ├── thirst_icon.png
│   │       ├── sleep_icon.png
│   │       ├── stress_icon.png
│   │       ├── willpower_icon.png
│   │       ├── inventory_bg.png
│   │       └── status_bar_bg.png
│   │
│   ├── maps/
│   │   ├── level_01.txt
│   │   ├── level_02.txt
│   │   ├── level_03.txt
│   │   └── ...                      # One text file per depth level
│   │
│   ├── data/
│   │   ├── creatures.json           # Creature stat definitions
│   │   ├── items.json               # Item definitions (all categories)
│   │   ├── spells.json              # Spell definitions
│   │   └── loot_tables.json         # Drop / spawn probability tables
│   │
│   └── sounds/                      # (future) SFX and ambient
│       └── ...
│
├── ecs/
│   ├── __init__.py
│   ├── world.py                     # World — entity registry + system scheduler
│   ├── entity.py                    # Entity — lightweight int ID wrapper
│   ├── component.py                 # Base Component dataclass + all component types
│   └── systems/
│       ├── __init__.py
│       ├── movement_system.py       # Validates & applies Position changes, collision
│       ├── combat_system.py         # Melee & ranged attack resolution
│       ├── magic_system.py          # Spell casting, mana cost, effects
│       ├── inventory_system.py      # Pick up, drop, equip, unequip, use
│       ├── survival_system.py       # Hunger, thirst, sleep, stress, willpower decay
│       ├── status_effect_system.py  # Buffs, debuffs, poison, regen tick
│       ├── ai_system.py             # Enemy AI: patrol, chase, flee, ability use
│       ├── fov_system.py            # Field-of-view / fog of war
│       ├── loot_system.py           # Item drop on creature death, chest contents
│       └── turn_system.py           # Turn order / initiative manager
│
├── core/
│   ├── __init__.py
│   ├── map_loader.py               # Parses level_XX.txt → tile grid + entity spawns
│   ├── map_generator.py            # (future) procedural level generation
│   ├── pathfinding.py              # A* for AI movement
│   ├── fov.py                      # Shadowcasting / raycasting algorithm
│   ├── dice.py                     # dN roll helpers (d4, d6, d20, etc.)
│   ├── formulas.py                 # Damage calc, to-hit, armor reduction, spell power
│   └── save_load.py                # Serialize/deserialize world state (JSON)
│
├── views/
│   ├── __init__.py
│   ├── title_view.py               # Main menu (New Game, Continue, Options, Quit)
│   ├── game_view.py                # Main gameplay — renders map, HUD, processes input
│   ├── inventory_view.py           # Inventory overlay / screen
│   ├── character_view.py           # Character sheet (stats, equipment slots)
│   ├── spellbook_view.py           # Known spells, cast from here or quick-bar
│   ├── game_over_view.py           # Death screen
│   └── message_log_view.py         # Scrollable combat / event log overlay
│
├── ui/
│   ├── __init__.py
│   ├── hud.py                      # Health, mana, survival bars, minimap
│   ├── message_log.py              # In-game scrolling text log
│   ├── tooltip.py                  # Hover / inspect info popup
│   └── popup_menu.py               # Context menu (use, equip, drop, inspect)
│
├── data/
│   ├── __init__.py
│   ├── creature_factory.py         # Builds creature entities from creatures.json
│   ├── item_factory.py             # Builds item entities from items.json
│   └── spell_registry.py           # Loads spells.json, resolves by ID
│
├── tests/
│   ├── test_ecs.py
│   ├── test_combat.py
│   ├── test_map_loader.py
│   ├── test_inventory.py
│   └── test_survival.py
│
├── docs/
│   ├── DESIGN_DOCUMENT.md          # ← This file
│   ├── ECS_GUIDE.md                # Deep-dive into the ECS architecture
│   ├── COMBAT_AND_MAGIC.md         # Combat formulas, spell system details
│   ├── MAP_FORMAT.md               # Map text file specification
│   └── CHANGELOG.md
│
├── requirements.txt                # arcade>=3.0, etc.
└── README.md
```

---

## 2. Map File Format (`assets/maps/level_XX.txt`)

Each level is a plain-text grid. The first line is metadata.

```
# LEVEL 1 — The East Gate — depth:1 width:60 height:30
############################################################
#........#.........#....................................#..#
#........#.........#....................................#..#
#...@....#....D....#........G.......G...................#..#
#........#.........#....................................#..#
####.#####....######....................................#..#
#..........>..#.........................................#..#
#.............#....................T.....................#..#
#..!..........#.........................................####
#.............#.........................................#
##############.#########################################
```

### Legend

| Char | Meaning               | Spawns                         |
|------|-----------------------|--------------------------------|
| `#`  | Wall                  | Wall tile                      |
| `.`  | Floor                 | Floor tile                     |
| `@`  | Player start          | Floor + player entity          |
| `>`  | Stairs down           | StairsDown tile                |
| `<`  | Stairs up             | StairsUp tile                  |
| `D`  | Door (closed)         | Door entity (Openable)         |
| `G`  | Goblin spawn          | Floor + Goblin entity          |
| `O`  | Orc spawn             | Floor + Orc entity             |
| `T`  | Troll spawn           | Floor + Troll entity           |
| `S`  | Spider spawn          | Floor + CaveSpider entity      |
| `W`  | Warg spawn            | Floor + Warg entity            |
| `B`  | Balrog spawn (boss)   | Floor + Balrog entity          |
| `!`  | Item drop point       | Floor + random item from loot  |
| `?`  | Trap (hidden)         | Floor + Trap entity            |
| `$`  | Chest                 | Floor + Chest entity           |
| `F`  | Fountain              | Floor + Fountain entity        |
| `A`  | Altar                 | Floor + Altar entity           |

---

## 3. Entity Component System (ECS) Design

### 3.1 Philosophy

The ECS follows a **simple, Pythonic** approach — no external ECS library needed.

- **Entity** = an integer ID (just `int`).
- **Component** = a `@dataclass` holding pure data, no logic.
- **System** = a function (or class) that queries the World for entities with specific component sets, then operates on them.
- **World** = the registry that maps `entity_id → {ComponentType: instance}` and runs systems each turn.

### 3.2 Core Components

```python
# ecs/component.py — excerpt of key components

@dataclass
class Position:
    x: int
    y: int
    depth: int              # dungeon level

@dataclass
class Renderable:
    texture_path: str
    layer: int = 0          # draw order (0=floor, 1=item, 2=creature, 3=player)
    color_tint: tuple = (255, 255, 255, 255)

@dataclass
class Player:
    """Tag component — marks the player entity."""
    name: str = "Adventurer"

@dataclass
class Stats:
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 8

@dataclass
class Health:
    current: int = 100
    maximum: int = 100

@dataclass
class Mana:
    current: int = 50
    maximum: int = 50

@dataclass
class SurvivalNeeds:
    hunger: float = 100.0       # 100 = full, 0 = starving
    thirst: float = 100.0       # 100 = hydrated, 0 = dehydrated
    sleep: float = 100.0        # 100 = rested, 0 = exhausted
    stress: float = 0.0         # 0 = calm, 100 = panic
    willpower: float = 100.0    # 0 = broken, 100 = resolute

@dataclass
class Inventory:
    items: list[int] = field(default_factory=list)   # entity IDs
    max_slots: int = 20

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

# ----- Item Components -----

@dataclass
class Item:
    """Tag: this entity is a pickable item."""
    name: str = ""
    description: str = ""
    weight: float = 0.1
    value: int = 0

@dataclass
class Consumable:
    """Used once then destroyed."""
    effect_type: str = ""       # "heal", "restore_mana", "food", "drink", "buff"
    potency: int = 0
    hunger_restore: float = 0.0
    thirst_restore: float = 0.0
    sleep_restore: float = 0.0
    stress_reduce: float = 0.0

@dataclass
class Equippable:
    slot: str = ""              # "weapon", "armor", "helmet", etc.
    armor_bonus: int = 0
    damage_dice: str = ""       # e.g. "2d6+3"
    damage_type: str = "physical"
    stat_bonuses: dict = field(default_factory=dict)  # {"strength": 2}
    special: str = ""           # e.g. "fire_damage", "mana_regen"

@dataclass
class SpellSource:
    """Item that teaches or casts a spell."""
    spell_id: str = ""
    source_type: str = "parchment"  # "parchment" (single-use) | "book" (permanent learn)
    charges: int = 1

# ----- Creature Components -----

@dataclass
class AI:
    behavior: str = "patrol"    # "patrol", "guard", "aggressive", "coward", "boss"
    aggro_range: int = 6
    patrol_path: list = field(default_factory=list)
    state: str = "idle"         # "idle", "chasing", "fleeing", "attacking", "casting"

@dataclass
class LootTable:
    table_id: str = ""          # references assets/data/loot_tables.json

@dataclass
class Experience:
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100
    xp_reward: int = 0          # given on death (for creatures)

@dataclass
class StatusEffects:
    effects: list = field(default_factory=list)
    # Each effect: {"id": "poison", "duration": 5, "potency": 3, "source": "spider_bite"}

@dataclass
class SpellKnowledge:
    known_spells: list[str] = field(default_factory=list)  # spell IDs

@dataclass
class Blocker:
    """Entity blocks movement (walls, closed doors, creatures)."""
    blocks_sight: bool = False

@dataclass
class Door:
    is_open: bool = False
    locked: bool = False
    key_id: str = ""

@dataclass
class StairsDown:
    target_depth: int = 0

@dataclass
class StairsUp:
    target_depth: int = 0

@dataclass
class Trap:
    trap_type: str = "spike"    # "spike", "poison_dart", "alarm", "teleport"
    damage: int = 10
    revealed: bool = False

@dataclass
class FieldOfView:
    radius: int = 8
    visible_tiles: set = field(default_factory=set)
```

### 3.3 World Registry

```python
# ecs/world.py — simplified

class World:
    def __init__(self):
        self._next_id: int = 0
        self._components: dict[int, dict[type, Any]] = {}  # eid → {CompType: instance}
        self._systems: list[System] = []

    def create_entity(self) -> int:
        eid = self._next_id; self._next_id += 1
        self._components[eid] = {}
        return eid

    def add_component(self, eid: int, component) -> None:
        self._components[eid][type(component)] = component

    def get_component(self, eid: int, comp_type: type):
        return self._components[eid].get(comp_type)

    def query(self, *comp_types) -> list[tuple[int, ...]]:
        """Return [(eid, comp1, comp2, ...) for entities having ALL listed types]."""
        results = []
        for eid, comps in self._components.items():
            if all(ct in comps for ct in comp_types):
                results.append((eid, *(comps[ct] for ct in comp_types)))
        return results

    def remove_entity(self, eid: int) -> None:
        self._components.pop(eid, None)

    def process_turn(self):
        """Run all registered systems in order."""
        for system in self._systems:
            system.process(self)
```

### 3.4 System Execution Order (per turn)

```
1. TurnSystem          — determine who acts this turn (initiative)
2. AISystem            — decide creature actions (move / attack / cast / flee)
3. MovementSystem      — resolve all queued moves, collision
4. CombatSystem        — resolve all queued attacks
5. MagicSystem         — resolve all queued spells
6. InventorySystem     — process pick-up / use / equip actions
7. StatusEffectSystem  — tick buffs/debuffs, apply poison, expire effects
8. SurvivalSystem      — decay hunger, thirst, sleep; apply consequences
9. LootSystem          — drop items from dead creatures
10. FOVSystem          — recompute player's visible area
```

---

## 4. Fight System

### 4.1 Turn-Based Combat

Combat is **tile-based, turn-based**. The player's move/action consumes their turn, then all creatures take their turn in initiative order.

### 4.2 Attack Resolution

```
To-Hit Roll:
    roll = d20 + attacker.Stats.dexterity_mod + weapon_bonus
    target_ac = 10 + target_armor_total + target.Stats.dexterity_mod
    HIT if roll >= target_ac

Damage:
    base_damage = roll_dice(weapon.damage_dice)       # e.g. "2d6+3"
    strength_mod = (attacker.Stats.strength - 10) // 2
    total_damage = base_damage + strength_mod
    damage_after_armor = max(1, total_damage - target_armor_reduction)

Critical Hit (natural 20):
    damage_dice rolled twice, strength_mod applied once

Miss (natural 1):
    Always miss, possible fumble effect (drop weapon, lose balance)
```

### 4.3 Melee vs Ranged

- **Melee:** attack adjacent tile (4-directional or 8-directional).
- **Ranged (bow/thrown):** player presses a fire key, then picks direction; projectile travels until hitting a blocker. Range stat on weapon. Line-of-sight required.

### 4.4 Creature Death

When `Health.current <= 0`:
1. `LootSystem` rolls on creature's `LootTable` → spawns item entities at creature's `Position`.
2. `Experience.xp_reward` added to player's `Experience.xp`.
3. Entity is removed from the World.

### 4.5 Armor Slots & Defense Calculation

```
total_armor = sum of all equipped Equippable.armor_bonus
    (weapon, armor, helmet, shield, gloves, boots, amulet, rings, talisman)

AC = 10 + total_armor + dexterity_mod
Damage reduction = total_armor // 3   (flat reduction after hit)
```

---

## 5. Sorcery / Magic System

### 5.1 Spell Acquisition

| Method | Component | Behavior |
|--------|-----------|----------|
| **Spell Parchment** | `SpellSource(source_type="parchment")` | Single-use: casts spell immediately, item consumed |
| **Spell Book** | `SpellSource(source_type="book")` | Use → spell added to `SpellKnowledge.known_spells` permanently, book consumed |
| **Innate (leveling)** | — | Some spells unlocked at XP level thresholds |

### 5.2 Casting

1. Player opens spellbook view or uses quick-bar hotkey.
2. Select spell → check `Mana.current >= spell.mana_cost`.
3. Target selection: self, directional, or area (depending on spell).
4. `MagicSystem` resolves effect.

### 5.3 Spell Categories & Examples

| Category | Spell | Mana | Effect |
|----------|-------|------|--------|
| **Offensive** | Flame Bolt | 8 | 3d6 fire damage, single target, range 6 |
| **Offensive** | Lightning Arc | 15 | 2d8 lightning, hits line of 3 tiles |
| **Offensive** | Shadow Word | 20 | 4d6 dark damage + fear (stress +30) |
| **Defensive** | Stone Skin | 10 | +5 armor for 10 turns |
| **Defensive** | Ward of Light | 12 | Repels undead in radius 3 for 8 turns |
| **Healing** | Healing Touch | 6 | Restores 2d8+4 HP |
| **Healing** | Purify | 8 | Removes poison, disease |
| **Utility** | Far Sight | 5 | FOV radius doubled for 15 turns |
| **Utility** | Teleport | 20 | Random safe tile on current level |
| **Utility** | Identify | 3 | Reveals item properties |
| **Buff** | Battle Fury | 14 | +4 STR, +2 attack for 8 turns, stress +10 |
| **Debuff** | Slow | 10 | Target loses every other turn for 6 turns |

### 5.4 Spell Power Scaling

```
spell_power = base_potency + (caster.Stats.intelligence - 10) // 2 + level_bonus
    level_bonus = caster.Experience.level // 3
For damage spells:
    damage = roll_dice(spell.dice) + spell_power
For healing:
    healing = roll_dice(spell.dice) + spell_power
```

---

## 6. Survival / Needs System

### 6.1 Decay Rates (per turn)

| Need | Decay/Turn | Danger Threshold | Critical Threshold | Consequence |
|------|-----------|-----------------|-------------------|-------------|
| Hunger | -0.15 | ≤ 25 | ≤ 10 | Danger: -1 STR. Critical: -1 HP/turn |
| Thirst | -0.20 | ≤ 25 | ≤ 10 | Danger: -2 to all rolls. Critical: -2 HP/turn |
| Sleep | -0.08 | ≤ 20 | ≤ 5 | Danger: FOV -2, miss chance +10%. Critical: random blackout (lose turn) |
| Stress | +0.05 (in combat +0.5) | ≥ 75 | ≥ 90 | Danger: willpower decays faster. Critical: panic (random movement) |
| Willpower | -0.03 (or faster if stressed) | ≤ 20 | ≤ 5 | Danger: spell cost +50%. Critical: cannot cast spells |

### 6.2 Restoration

- **Food:** bread (+20 hunger), meat (+35), lembas (+60 hunger, +10 willpower)
- **Drink:** water flask (+30 thirst), ale (+25 thirst, -5 stress, -5 willpower), miruvor (+50 thirst, +20 willpower, +10 mana), ent draught (+80 thirst, +40 hunger, +20 HP)
- **Sleep:** resting at safe tiles (altar, cleared rooms) — skips N turns, restores sleep
- **Stress reduction:** fountains, ale, certain spells, leveling up
- **Willpower:** miruvor, lembas, altars, prayer at altars

---

## 7. Creature Bestiary (Moria / Tolkien-Inspired)

| Creature | Depth | HP | Armor | Damage | AI | Special |
|----------|-------|-----|-------|--------|-----|---------|
| Goblin | 1-4 | 15 | 2 | 1d4 | aggressive | Packs: +1 atk per adjacent goblin |
| Orc | 2-6 | 30 | 5 | 1d8+1 | aggressive | Rage: +2 dmg when HP < 50% |
| Cave Spider | 1-5 | 12 | 1 | 1d4 | aggressive | Poison bite (2 dmg/turn, 4 turns) |
| Warg | 3-7 | 35 | 3 | 2d4+2 | aggressive | Leap attack (2-tile range) |
| Uruk-hai | 5-8 | 50 | 8 | 2d6+3 | aggressive | Sunlight-resistant, high morale |
| Cave Troll | 4-8 | 80 | 10 | 2d8+4 | guard | Slow (acts every 2 turns), area smash |
| Barrow-wight | 6-9 | 40 | 6 | 1d6+2 | aggressive | Paralyze gaze, drains willpower |
| Nazgûl Shadow | 8-10 | 70 | 12 | 2d8+5 | boss | Fear aura (stress +15/turn), magic resist |
| Dragon-worm | 7-10 | 60 | 14 | 3d6 fire | guard | Fire breath (cone, 3d8 fire) |
| **Durin's Bane (Balrog)** | 10 | 200 | 18 | 3d10+8 | boss | Fire whip (range 3), flame aura, fear |

---

## 8. Item Categories — ECS Composition

Each item is an entity composed of relevant components:

### Example Compositions

```
Sword of Gondolin:
    Item(name="Sword of Gondolin", weight=3.0, value=500)
    Equippable(slot="weapon", damage_dice="2d6+2", damage_type="physical",
               stat_bonuses={"strength": 1}, special="glow_near_orcs")
    Position(x=10, y=5, depth=3)
    Renderable(texture_path="assets/textures/items/weapons/sword.png", layer=1)

Lembas Bread:
    Item(name="Lembas Bread", weight=0.2, value=80)
    Consumable(effect_type="food", hunger_restore=60.0, willpower_restore=10.0)
    Position(x=4, y=12, depth=1)
    Renderable(texture_path="assets/textures/items/consumables/lembas.png", layer=1)

Scroll of Flame Bolt:
    Item(name="Scroll of Flame Bolt", weight=0.1, value=120)
    SpellSource(spell_id="flame_bolt", source_type="parchment", charges=1)
    Position(x=8, y=3, depth=2)
    Renderable(texture_path="assets/textures/items/magic/spell_parchment.png", layer=1)

Ring of Protection:
    Item(name="Ring of Protection", weight=0.05, value=300)
    Equippable(slot="ring_left", armor_bonus=3, stat_bonuses={"constitution": 2})
    Position(x=15, y=7, depth=5)
    Renderable(texture_path="assets/textures/items/magic/ring.png", layer=1)
```

### Slot → Category Mapping

| Slot | Item Types |
|------|-----------|
| `weapon` | Sword, Axe, Bow, Staff, Dagger, Mace |
| `armor` | Leather, Chainmail, Plate |
| `helmet` | Helm, Hood, Crown |
| `shield` | Buckler, Round Shield, Tower Shield |
| `gloves` | Gloves, Gauntlets |
| `boots` | Boots, Greaves |
| `amulet` | Amulet (one slot) |
| `ring_left`, `ring_right` | Rings (two slots) |
| `talisman` | Talisman (one slot) |
| *(not equippable)* | Food, Drink, Parchment, Spell Book, Keys, Gold |

---

## 9. Arcade 3.x Integration Notes

### 9.1 Views

Arcade 3.x uses `arcade.View` subclasses for screens. Each view in `views/` extends `arcade.View` and implements:
- `on_show_view()` — setup when view becomes active
- `on_draw()` — render frame
- `on_key_press()` / `on_key_release()` — input
- `on_update(delta_time)` — per-frame logic (animation, not game turns)

### 9.2 Tile Rendering

- Use `arcade.SpriteList` for each layer (floor, items, creatures, player).
- On level load or FOV change, rebuild sprite lists from ECS queries:
  `world.query(Position, Renderable)` filtered by `depth == current_depth`.
- Camera centered on player: `arcade.Camera2D`.

### 9.3 Turn Loop

The game is **turn-based**, not real-time. The game loop:
1. Wait for player input (arrow keys = move, other keys = action).
2. Player action is queued.
3. `world.process_turn()` runs all systems.
4. Render updated state.
5. Go to 1.

### 9.4 Arrow Key Movement

```python
def on_key_press(self, key, modifiers):
    dx, dy = 0, 0
    if key == arcade.key.UP:    dy = 1
    elif key == arcade.key.DOWN:  dy = -1
    elif key == arcade.key.LEFT:  dx = -1
    elif key == arcade.key.RIGHT: dx = 1

    if dx or dy:
        # Queue move intent, then process turn
        self.world.player_intent = ("move", dx, dy)
        self.world.process_turn()
```

---

## 10. Current State & Development Roadmap

### Phase 1 — Foundation (Current Target) ✅ PLANNED

| Task | Status | Priority |
|------|--------|----------|
| Project structure & folder tree | 🟡 Designed | P0 |
| `constants.py`, `main.py`, `game_engine.py` | ⬜ Not started | P0 |
| ECS core (`World`, `Entity`, `Component`) | ⬜ Not started | P0 |
| Map loader (`level_XX.txt` → tile grid) | ⬜ Not started | P0 |
| Basic rendering (floor, walls, player sprite) | ⬜ Not started | P0 |
| Player movement (arrow keys, collision) | ⬜ Not started | P0 |
| Camera follow player | ⬜ Not started | P0 |
| Stairs / multi-depth level transitions | ⬜ Not started | P0 |

### Phase 2 — Core Gameplay

| Task | Status | Priority |
|------|--------|----------|
| FOV / fog of war | ⬜ Not started | P1 |
| Enemy spawning from map | ⬜ Not started | P1 |
| Basic AI (chase player, patrol) | ⬜ Not started | P1 |
| Combat system (melee hit/damage) | ⬜ Not started | P1 |
| Health bar HUD | ⬜ Not started | P1 |
| Creature death & removal | ⬜ Not started | P1 |
| Message log (combat events) | ⬜ Not started | P1 |

### Phase 3 — Items & Inventory

| Task | Status | Priority |
|------|--------|----------|
| Item entities on map | ⬜ Not started | P2 |
| Pick up (walk over or key press) | ⬜ Not started | P2 |
| Inventory screen (list, inspect) | ⬜ Not started | P2 |
| Equip / unequip to slots | ⬜ Not started | P2 |
| Consumable use (food, drink, potions) | ⬜ Not started | P2 |
| Equipment affects combat stats | ⬜ Not started | P2 |
| Loot drops from creatures | ⬜ Not started | P2 |

### Phase 4 — Magic & Spells

| Task | Status | Priority |
|------|--------|----------|
| Mana bar HUD | ⬜ Not started | P2 |
| Spell parchment (single-use cast) | ⬜ Not started | P2 |
| Spell book (learn permanently) | ⬜ Not started | P2 |
| Spellbook view (known spells) | ⬜ Not started | P2 |
| Targeting system (directional, AoE) | ⬜ Not started | P2 |
| Status effects (buff/debuff/poison) | ⬜ Not started | P2 |

### Phase 5 — Survival & Polish

| Task | Status | Priority |
|------|--------|----------|
| Survival needs (hunger, thirst, sleep) | ⬜ Not started | P3 |
| Stress & willpower system | ⬜ Not started | P3 |
| Survival HUD bars | ⬜ Not started | P3 |
| Traps, chests, doors, fountains, altars | ⬜ Not started | P3 |
| Ranged combat (bows) | ⬜ Not started | P3 |
| Save / load game | ⬜ Not started | P3 |
| Character creation / class selection | ⬜ Not started | P3 |
| Game over screen | ⬜ Not started | P3 |

### Phase 6 — Advanced

| Task | Status | Priority |
|------|--------|----------|
| Advanced AI (flee, call allies, use abilities) | ⬜ Not started | P4 |
| Procedural map generation | ⬜ Not started | P4 |
| Sound effects & ambient audio | ⬜ Not started | P4 |
| Boss encounters (Balrog) | ⬜ Not started | P4 |
| Multiple player classes | ⬜ Not started | P4 |
| Tooltips & context menus | ⬜ Not started | P4 |

---

## 11. Key Design Decisions

1. **Why ECS?** — Decouples data from behavior. Adding a new item type = new component composition, no class hierarchy changes. Systems are modular and testable.

2. **Why text-file maps?** — Easy to author by hand, version-controllable, human-readable. Procedural generation is planned for later as an alternative.

3. **Why turn-based?** — Classic roguelike feel. Allows thoughtful tactical play. Simpler to implement correctly than real-time with ECS.

4. **Why Arcade 3.x?** — Pythonic, well-documented, sprite-based (perfect for tile games), built-in camera, good enough performance for 2D grid games, active maintenance.

5. **Survival needs** — Adds tension and resource management beyond combat. Food/water become strategic decisions. Stress/willpower ties into the oppressive atmosphere of Moria.

---

*Document version: 0.1 — Initial design*
*Next step: Implement Phase 1 foundation code*
