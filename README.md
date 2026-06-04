# Depths of Moria

A turn-based roguelike dungeon crawler set in Tolkien's Mines of Moria.
Built with **Python 3.11+** and **Arcade 3.x**.

## Quick Start

```bash
pip install arcade>=3.0
cd moria_depths
python main.py
```

## Controls (press H in-game for full list)

| Key | Action |
|-----|--------|
| Arrow keys | Move / melee attack (bump into enemy) |
| R + Arrow | Ranged attack (needs bow/crossbow equipped + ammo) |
| > / < | Descend / ascend stairs |
| G | Pick up item |
| E | Interact (fountain, altar, chest) |
| I | Inventory (U=use, E=equip, D=drop) |
| C | Character sheet |
| H | Help overlay |
| F | Toggle fullscreen |
| Space | Wait one turn |
| Escape | Quit to title / cancel |

## How To...

**Drink water:** Press I (inventory) → select Water Flask → press U (use)

**Switch weapons:** Press I → select weapon → press E (equip). Old weapon goes to pack.

**Shoot enemies:** Equip a bow via inventory (I→E), make sure you have arrows, press R then an Arrow key.

**Open locked doors:** Find the matching colored key on the map, pick it up (G), then walk into the locked door.

**Descend deeper:** Find the stairs (>) and press > (Shift+.) while standing on them.

## Documentation

- `docs/CURRENT_STATE.md` — Full feature list and project status
- `docs/ARCADE_3X_MIGRATION.md` — Arcade 2.x→3.x API migration guide
- `docs/DESIGN_DOCUMENT.md` — Original game design document

## Tests

```bash
python tests/test_ecs.py       # 10 tests — ECS core, dice, map loading
python tests/test_combat.py    # 9 tests — combat, AI, inventory, survival
```
