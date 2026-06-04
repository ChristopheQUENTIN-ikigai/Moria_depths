"""
Depths of Moria — Global constants and configuration.
"""

# ── Window ──────────────────────────────────────────────
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Depths of Moria"

# ── Tile grid ───────────────────────────────────────────
TILE_SIZE = 32
HALF_TILE = TILE_SIZE // 2

# ── Sprite draw layers (lower = drawn first) ───────────
LAYER_FLOOR = 0
LAYER_ITEM = 1
LAYER_CREATURE = 2
LAYER_PLAYER = 3
LAYER_PROJECTILE = 4

# ── Colors (R, G, B) or (R, G, B, A) ──────────────────
COLOR_BG = (15, 15, 20)
COLOR_WALL = (90, 80, 75)
COLOR_FLOOR = (50, 45, 42)
COLOR_FLOOR_LIT = (70, 65, 58)
COLOR_PLAYER = (60, 180, 255)
COLOR_ENEMY = (220, 50, 50)
COLOR_ITEM_COLOR = (255, 215, 0)
COLOR_STAIRS_DOWN = (0, 200, 120)
COLOR_STAIRS_UP = (120, 200, 0)
COLOR_DOOR_CLOSED = (160, 110, 50)
COLOR_DOOR_OPEN = (100, 70, 35)
COLOR_TRAP = (200, 50, 200)
COLOR_CHEST = (210, 170, 60)
COLOR_FOUNTAIN = (80, 140, 220)
COLOR_ALTAR = (220, 220, 180)
COLOR_FOG = (30, 30, 40, 180)
COLOR_UNEXPLORED = (0, 0, 0, 255)

# ── Key colors (for locked doors) ──────────────────────
KEY_COLORS = {
    "red":    (220, 50, 50),
    "blue":   (50, 100, 220),
    "green":  (50, 200, 80),
    "yellow": (220, 200, 50),
    "purple": (160, 60, 200),
}

# ── HUD ─────────────────────────────────────────────────
HUD_HEIGHT = 130
HUD_BAR_WIDTH = 160
HUD_BAR_HEIGHT = 14
HUD_PADDING = 8

COLOR_HP_BAR = (200, 40, 40)
COLOR_HP_BG = (80, 20, 20)
COLOR_MANA_BAR = (40, 80, 200)
COLOR_MANA_BG = (20, 30, 80)
COLOR_HUNGER_BAR = (180, 130, 40)
COLOR_HUNGER_BG = (70, 50, 20)
COLOR_THIRST_BAR = (40, 150, 200)
COLOR_THIRST_BG = (20, 60, 80)
COLOR_SLEEP_BAR = (120, 80, 180)
COLOR_SLEEP_BG = (50, 30, 70)
COLOR_STRESS_BAR = (200, 100, 40)
COLOR_STRESS_BG = (80, 40, 20)
COLOR_WILLPOWER_BAR = (200, 200, 80)
COLOR_WILLPOWER_BG = (80, 80, 30)
COLOR_XP_BAR = (80, 200, 80)
COLOR_XP_BG = (30, 80, 30)

# ── FOV ─────────────────────────────────────────────────
DEFAULT_FOV_RADIUS = 8

# ── Survival decay per turn ─────────────────────────────
HUNGER_DECAY = 0.15
THIRST_DECAY = 0.20
SLEEP_DECAY = 0.08
STRESS_PASSIVE_GAIN = 0.05
STRESS_COMBAT_GAIN = 0.50
WILLPOWER_DECAY = 0.03

SURVIVAL_DANGER = 25.0
SURVIVAL_CRITICAL = 10.0
STRESS_DANGER = 75.0
STRESS_CRITICAL = 90.0
WILLPOWER_DANGER = 20.0
WILLPOWER_CRITICAL = 5.0

# ── Combat ──────────────────────────────────────────────
BASE_AC = 10
CRIT_ROLL = 20
FUMBLE_ROLL = 1
MAX_RANGED_RANGE = 10

# ── XP ──────────────────────────────────────────────────
XP_BASE = 100
XP_FACTOR = 1.5

# ── Message log ─────────────────────────────────────────
MAX_LOG_MESSAGES = 200
LOG_VISIBLE_LINES = 5

# ── Inventory ───────────────────────────────────────────
DEFAULT_INVENTORY_SLOTS = 20

# ── Map character legend ────────────────────────────────
MAP_CHARS: dict[str, str] = {
    "#": "wall",
    ".": "floor",
    "@": "player_start",
    ">": "stairs_down",
    "<": "stairs_up",
    "D": "door",
    "1": "door_red",
    "2": "door_blue",
    "3": "door_green",
    "4": "door_yellow",
    "5": "door_purple",
    "G": "goblin",
    "O": "orc",
    "T": "troll",
    "S": "spider",
    "W": "warg",
    "U": "uruk_hai",
    "B": "balrog",
    "N": "nazgul",
    "R": "dragon_worm",
    "H": "barrow_wight",
    "!": "item_spawn",
    "?": "trap",
    "$": "chest",
    "F": "fountain",
    "A": "altar",
    "C": "gold_pile",
    "r": "key_red",
    "b": "key_blue",
    "g": "key_green",
    "y": "key_yellow",
    "p": "key_purple",
}

# ── Help text ───────────────────────────────────────────
HELP_TEXT = [
    ("MOVEMENT", [
        ("Arrow keys", "Move / bump-attack adjacent enemy"),
        ("Space", "Wait one turn"),
    ]),
    ("EXPLORATION", [
        ("> (Shift+.)", "Descend stairs"),
        ("< (Shift+,)", "Ascend stairs"),
        ("E", "Interact (fountain / altar / chest)"),
        ("G", "Pick up item at feet"),
    ]),
    ("COMBAT", [
        ("Bump into enemy", "Melee attack"),
        ("R then Arrow key", "Ranged attack (bow/crossbow) — needs ammo"),
    ]),
    ("INVENTORY & CHARACTER", [
        ("I", "Open inventory"),
        ("  U", "  Use selected item (eat food, drink, read scroll)"),
        ("  E", "  Equip selected item"),
        ("  D", "  Drop selected item"),
        ("C", "Character sheet (stats, equipment, spells)"),
    ]),
    ("SYSTEM", [
        ("H", "Show / hide this help"),
        ("F", "Toggle fullscreen"),
        ("Escape", "Quit to title"),
    ]),
]
