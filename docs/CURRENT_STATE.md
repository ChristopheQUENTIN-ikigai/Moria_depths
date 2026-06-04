# Depths of Moria — Current State of Development

**Version:** Phase 1 Complete (v0.5.0)
**Engine:** Python 3.11+ / Arcade 3.x
**Architecture:** Custom Entity Component System (ECS) — no external ECS library

---

## Implemented Features

### Core Systems (ECS)

| System | Status | Description |
|--------|--------|-------------|
| **MovementSystem** | Done | Arrow key movement, collision, door opening (plain + colored locked), auto gold pickup, item/stair hints |
| **CombatSystem** | Done | d20 melee (bump-attack), ranged attacks (bow/crossbow + ammo), crits/fumbles, death/XP/leveling |
| **AISystem** | Done | State machine: idle → chasing → attacking → fleeing. Creatures pathfind toward player |
| **InventorySystem** | Done | Pick up (G), use consumable (U), equip/unequip (E), drop (D). Weapon swapping returns old weapon to pack |
| **StatusEffectSystem** | Done | Ticks poison/regen/bleed, decrements duration, removes expired effects |
| **SurvivalSystem** | Done | Hunger, thirst, sleep, stress, willpower decay each turn. Consequences at danger/critical thresholds |
| **FOVSystem** | Done | Raycasting field of view. Visible tiles + explored tiles (fog of war memory) |

### Player Controls

| Key | Action | Notes |
|-----|--------|-------|
| Arrow keys | Move / bump-attack | Moving into enemy = melee attack |
| > (Shift+.) | Descend stairs | Must be standing on stairs down |
| < (Shift+,) | Ascend stairs | Must be standing on stairs up |
| G | Pick up item | Picks up item at player's feet |
| E | Interact | Use fountain (drink), altar (pray), chest (open) |
| R then Arrow | Ranged attack | Requires equipped ranged weapon + matching ammo |
| I | Open inventory | Sub-keys: U=use, E=equip, D=drop, ESC=close |
| C | Character sheet | Stats, equipment, survival bars, known spells |
| H | Toggle help overlay | Shows all key bindings and gameplay tips |
| F | Toggle fullscreen | |
| Space | Wait one turn | |
| Escape | Quit to title | Also cancels ranged mode and closes help |

### Combat Mechanics

- **Melee:** Walk into enemy. d20 + DEX_mod vs AC (10 + armor + DEX_mod). Damage = weapon_dice + STR_mod - (armor/3)
- **Ranged:** Press R, then arrow direction. Projectile traces straight line up to 10 tiles. Needs matching ammo (arrows for bows, bolts for crossbows). Uses DEX_mod for both hit and damage
- **Critical Hit:** Natural 20 — double damage dice
- **Fumble:** Natural 1 — automatic miss
- **Death:** Creature dies → XP awarded, gold drop chance. Player dies → Game Over screen

### Weapon System

- Player starts with Iron Sword (melee, 1d6+1) equipped + Short Bow (ranged, 1d6) + 15 arrows in inventory
- **Switching weapons:** Open inventory (I), select a weapon, press E to equip. The previously equipped weapon is returned to your pack
- **Finding weapons:** Weapons and ammo spawn on '!' item points (30% chance weapon/ammo, 70% consumable)
- **Weapon types found:** Short Bow (ranged/arrow), Crossbow (ranged/bolt), Battle Axe (melee), Mace (melee), Elven Dagger (melee)
- **Ammo:** Arrows and Bolts found on map. Stack count shown in inventory. Consumed on each ranged shot

### Colored Key / Locked Door System

- Doors can be **plain** (D on map) or **color-locked** (1=red, 2=blue, 3=green, 4=yellow, 5=purple)
- Color-locked doors display in their key color and require a matching colored key to open
- Keys are found on the map (r=red, b=blue, g=green, y=yellow, p=purple)
- Walking into a locked door with the correct key in inventory automatically unlocks it, consuming the key
- Walking into a locked door without the key shows a message: "The door is locked. You need a [Color] Key."

### Survival Needs

| Need | Decay/Turn | Danger | Critical | Effect at Critical |
|------|-----------|--------|----------|-------------------|
| Hunger | -0.15 | 25 | 10 | HP loss each turn |
| Thirst | -0.20 | 25 | 10 | HP loss each turn |
| Sleep | -0.08 | 25 | 10 | Warning messages |
| Stress | +0.05 | 75 | 90 | Willpower drain |
| Willpower | -0.03 | 20 | 5 | Penalty warnings |

**How to manage survival:**
- **Hunger:** Eat food items (Bread, Meat, Lembas) via inventory U key
- **Thirst:** Drink Water Flask or Ale via inventory U key, or use fountain (E key)
- **Willpower/Stress:** Pray at altars (E key), drink Miruvor
- **HP:** Healing Herbs, Ent Draught, fountain, or level up

### Dungeon Levels

| Level | Name | Key Enemies | Special | Key Required |
|-------|------|-------------|---------|-------------|
| 1 | The East Gate | Goblins (4) | 2 fountains, altar | Red key → red door |
| 2 | Goblin Warrens | Goblins (5), Troll | Chest, fountain | Blue key → blue door |
| 3 | The Deep Halls | Orcs, Warg, Uruk-hai | 2 fountains, traps | Green key → green door |
| 4 | Bridge of Khazad-dum | Wargs, Uruk-hai, Nazgûl, **Balrog** | Boss room | Purple key → purple door |

### Creature Bestiary

| Species | HP | Damage | XP | Behavior |
|---------|----|---------|----|----------|
| Goblin | 15 | 1d4 | 10 | Aggressive |
| Orc | 30 | 1d8+1 | 25 | Aggressive |
| Troll | 80 | 2d8+4 | 80 | Guard |
| Spider | 12 | 1d4 | 8 | Aggressive |
| Warg | 35 | 2d4+2 | 30 | Aggressive |
| Uruk-hai | 50 | 2d6+3 | 55 | Aggressive |
| Barrow-wight | 40 | 1d6+2 | 60 | Aggressive |
| Nazgûl | 70 | 2d8+5 | 120 | Boss |
| Dragon Worm | 60 | 3d6 | 100 | Guard |
| **Balrog** | **200** | **3d10+8** | **500** | **Boss** |

### Rendering

- **SpriteList-based** (proper Arcade 3.x pattern)
- 55 hand-generated 32×32 pixel-art JPG textures in `assets/textures/`
- Automatic fallback to solid-color rectangles if texture files are missing
- FOV: visible tiles at full brightness, explored tiles dimmed (alpha=80), unexplored = black
- Camera scrolls to center on player. HUD drawn with fixed camera

### UI Screens

| Screen | Description |
|--------|-------------|
| **Title** | New Game, Fullscreen toggle, Quit |
| **Game** | Main dungeon view with scrolling camera + HUD |
| **Help Overlay** | All key bindings + gameplay tips (H to toggle) |
| **Inventory** | Item list with tags (damage, ammo count, consumable effects) |
| **Character** | Stats, equipment, survival bars, known spells |
| **Game Over** | Death summary with level/depth/turn, restart or quit |

---

## Project Structure

```
moria_depths/
├── main.py                        Entry point
├── constants.py                   All config, key bindings, map legend
├── generate_textures.py           Regenerate 55 sample textures
├── requirements.txt               arcade>=3.0
├── ecs/
│   ├── world.py                   Central registry + system scheduler
│   ├── entity.py                  Entity ID wrapper
│   ├── component.py               All dataclass components
│   └── systems/
│       ├── movement_system.py     Movement, doors, keys, collision
│       ├── combat_system.py       Melee + ranged + damage + death
│       ├── ai_system.py           Creature AI state machine
│       ├── inventory_system.py    Pickup, use, equip, drop
│       ├── status_effect_system.py  Poison, regen, bleed ticking
│       ├── survival_system.py     Hunger/thirst/sleep/stress decay
│       └── fov_system.py          Raycasting FOV
├── core/
│   ├── map_loader.py              Text map parser + entity spawning
│   ├── dice.py                    "2d6+3" notation roller
│   └── pathfinding.py             Distance + step-toward
├── views/
│   ├── title_view.py              Main menu
│   ├── game_view.py               Gameplay + rendering + input
│   ├── inventory_view.py          Inventory overlay
│   ├── character_view.py          Character sheet
│   └── game_over_view.py          Death screen
├── ui/
│   └── hud.py                     HP/mana/survival bars, message log
├── assets/
│   ├── maps/                      4 level text files
│   └── textures/                  55 JPG textures (32×32 pixel art)
├── tests/
│   ├── test_ecs.py                ECS core + dice + map loading
│   └── test_combat.py             Combat + AI + inventory + survival
└── docs/
    ├── DESIGN_DOCUMENT.md         Full game design document
    ├── ARCADE_3X_MIGRATION.md     Arcade 2.x→3.x API changes
    └── CURRENT_STATE.md           This file
```

---

## Not Yet Implemented (Roadmap)

| Feature | Priority | Notes |
|---------|----------|-------|
| Magic system | High | SpellKnowledge component exists. Need casting UI, mana costs, spell effects |
| Procedural map generation | High | Currently hand-authored text maps |
| Trap triggering | Medium | Trap component exists but stepping on traps has no effect yet |
| Save/load | Medium | Serialize World state to JSON |
| Sound effects | Low | Arcade 3.x supports `arcade.Sound` |
| Sprite animations | Low | Currently static textures |
| More dungeon levels | Medium | Currently 4 levels, easily add more via text files |
| NPC dialogue | Low | |
| Enchantment system | Low | Equippable.special field exists but unused |
| Multiple player classes | Low | Mage/Ranger textures generated but not selectable |

---

## Test Coverage

19 tests across 2 test files, all passing:

**test_ecs.py (10 tests):** Entity lifecycle, components CRUD, multi-component query, blocking/sight, spatial queries, dice rolls, stat modifiers, health properties, message log, full map loading

**test_combat.py (9 tests):** Player melee attack, creature death + XP, wall collision, item pickup, consumable use, equip/unequip cycle, survival decay, AI chase behavior, status effect tick + expiry
