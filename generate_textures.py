#!/usr/bin/env python3
"""
Generate sample 32x32 pixel-art textures (JPG) for Depths of Moria.

Run:  python generate_textures.py
"""
import os
from PIL import Image, ImageDraw

BASE = os.path.join(os.path.dirname(__file__), "assets", "textures")
SIZE = 32


def make(subpath: str, draw_fn):
    """Create a 32x32 image, run draw_fn on it, save as JPG."""
    path = os.path.join(BASE, subpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_fn(draw, img)
    img.save(path, "JPEG", quality=90)


def fill(draw, img, color):
    draw.rectangle([0, 0, SIZE - 1, SIZE - 1], fill=color)


def fill_with_border(draw, img, fill_color, border_color, bw=1):
    draw.rectangle([0, 0, SIZE - 1, SIZE - 1], fill=fill_color, outline=border_color, width=bw)


def center_rect(draw, img, outer, inner, inner_color):
    draw.rectangle([0, 0, SIZE - 1, SIZE - 1], fill=outer)
    m = (SIZE - inner) // 2
    draw.rectangle([m, m, m + inner - 1, m + inner - 1], fill=inner_color)


# ════════════════════════════════════════════════
# TILES
# ════════════════════════════════════════════════

def tile_floor_stone(d, i):
    d.rectangle([0, 0, 31, 31], fill=(50, 45, 42))
    # subtle stone texture dots
    for px, py in [(5, 5), (15, 10), (25, 7), (8, 22), (20, 25), (28, 18), (12, 16)]:
        d.point((px, py), fill=(60, 55, 50))
    for px, py in [(3, 14), (18, 3), (27, 27), (10, 28)]:
        d.point((px, py), fill=(40, 38, 35))

def tile_wall_stone(d, i):
    d.rectangle([0, 0, 31, 31], fill=(90, 80, 75))
    # brick lines
    d.line([(0, 10), (31, 10)], fill=(70, 62, 58), width=1)
    d.line([(0, 21), (31, 21)], fill=(70, 62, 58), width=1)
    d.line([(15, 0), (15, 10)], fill=(70, 62, 58), width=1)
    d.line([(8, 10), (8, 21)], fill=(70, 62, 58), width=1)
    d.line([(24, 10), (24, 21)], fill=(70, 62, 58), width=1)
    d.line([(15, 21), (15, 31)], fill=(70, 62, 58), width=1)

def tile_wall_mossy(d, i):
    tile_wall_stone(d, i)
    for px, py in [(3, 26), (5, 28), (7, 25), (20, 27), (22, 29), (14, 30)]:
        d.point((px, py), fill=(40, 100, 40))
        d.point((px + 1, py), fill=(50, 110, 50))

def tile_door_closed(d, i):
    d.rectangle([0, 0, 31, 31], fill=(50, 45, 42))  # floor bg
    d.rectangle([4, 2, 27, 29], fill=(140, 95, 45))  # door
    d.rectangle([5, 3, 26, 28], fill=(160, 110, 50), outline=(120, 80, 35))
    # handle
    d.ellipse([20, 13, 24, 17], fill=(200, 180, 60))

def tile_door_open(d, i):
    d.rectangle([0, 0, 31, 31], fill=(50, 45, 42))
    d.rectangle([0, 2, 7, 29], fill=(100, 70, 35))  # door swung open to left
    d.rectangle([1, 3, 6, 28], fill=(120, 85, 40))

def tile_stairs_down(d, i):
    d.rectangle([0, 0, 31, 31], fill=(50, 45, 42))
    # descending steps
    for j in range(5):
        y = 4 + j * 5
        shade = 60 - j * 10
        d.rectangle([4 + j * 2, y, 27 - j * 2, y + 3], fill=(shade, max(shade - 5, 0), max(shade - 8, 0)))
    # arrow indicator
    d.polygon([(14, 28), (17, 28), (15, 31)], fill=(0, 200, 120))

def tile_stairs_up(d, i):
    d.rectangle([0, 0, 31, 31], fill=(50, 45, 42))
    for j in range(5):
        y = 26 - j * 5
        shade = 40 + j * 10
        d.rectangle([4 + j * 2, y, 27 - j * 2, y + 3], fill=(shade, max(shade - 5, 0), max(shade - 8, 0)))
    d.polygon([(14, 3), (17, 3), (15, 0)], fill=(120, 200, 0))

def tile_trap_hidden(d, i):
    # looks like normal floor
    tile_floor_stone(d, i)

def tile_trap_revealed(d, i):
    d.rectangle([0, 0, 31, 31], fill=(50, 45, 42))
    d.line([(8, 8), (23, 23)], fill=(200, 50, 200), width=2)
    d.line([(23, 8), (8, 23)], fill=(200, 50, 200), width=2)

def tile_chest(d, i):
    d.rectangle([0, 0, 31, 31], fill=(50, 45, 42))
    d.rectangle([6, 10, 25, 25], fill=(180, 140, 40), outline=(140, 100, 20), width=1)
    d.rectangle([6, 10, 25, 15], fill=(200, 160, 50))  # lid
    d.rectangle([14, 17, 17, 20], fill=(220, 200, 60))  # lock

def tile_fountain(d, i):
    d.rectangle([0, 0, 31, 31], fill=(50, 45, 42))
    d.ellipse([6, 10, 25, 27], fill=(40, 80, 140))
    d.ellipse([8, 12, 23, 25], fill=(60, 120, 200))
    # water sparkle
    d.point((14, 16), fill=(180, 220, 255))
    d.point((17, 19), fill=(180, 220, 255))

def tile_altar(d, i):
    d.rectangle([0, 0, 31, 31], fill=(50, 45, 42))
    d.rectangle([8, 14, 23, 28], fill=(180, 175, 160))  # base
    d.rectangle([6, 10, 25, 14], fill=(200, 195, 180))   # top slab
    # candle flame
    d.ellipse([14, 4, 17, 9], fill=(255, 220, 80))
    d.point((15, 3), fill=(255, 255, 180))


# ════════════════════════════════════════════════
# PLAYER
# ════════════════════════════════════════════════

def player_warrior(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    # body
    d.rectangle([12, 10, 19, 24], fill=(50, 100, 170))
    # head
    d.ellipse([12, 3, 19, 10], fill=(220, 180, 140))
    # legs
    d.rectangle([12, 24, 15, 30], fill=(60, 50, 40))
    d.rectangle([16, 24, 19, 30], fill=(60, 50, 40))
    # sword
    d.line([(22, 6), (22, 22)], fill=(200, 200, 210), width=2)
    d.line([(20, 14), (24, 14)], fill=(160, 140, 80), width=1)

def player_mage(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.rectangle([12, 10, 19, 24], fill=(80, 40, 120))
    d.ellipse([12, 3, 19, 10], fill=(220, 180, 140))
    d.rectangle([12, 24, 15, 30], fill=(60, 40, 80))
    d.rectangle([16, 24, 19, 30], fill=(60, 40, 80))
    # staff
    d.line([(24, 2), (24, 28)], fill=(120, 80, 40), width=2)
    d.ellipse([22, 0, 26, 4], fill=(100, 160, 255))

def player_ranger(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.rectangle([12, 10, 19, 24], fill=(50, 100, 50))
    d.ellipse([12, 3, 19, 10], fill=(220, 180, 140))
    d.rectangle([12, 24, 15, 30], fill=(60, 50, 30))
    d.rectangle([16, 24, 19, 30], fill=(60, 50, 30))
    # bow
    d.arc([21, 6, 27, 22], 270, 90, fill=(120, 80, 40), width=2)
    d.line([(24, 6), (24, 22)], fill=(180, 170, 140), width=1)


# ════════════════════════════════════════════════
# CREATURES
# ════════════════════════════════════════════════

def creature(d, i, body_color, eye_color=(255, 0, 0), has_weapon=False, big=False):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    if big:
        d.rectangle([8, 8, 23, 26], fill=body_color)
        d.ellipse([9, 2, 22, 12], fill=body_color)
        d.point((12, 6), fill=eye_color); d.point((19, 6), fill=eye_color)
        d.rectangle([9, 26, 14, 31], fill=(max(body_color[0]-30,0), max(body_color[1]-30,0), max(body_color[2]-30,0)))
        d.rectangle([17, 26, 22, 31], fill=(max(body_color[0]-30,0), max(body_color[1]-30,0), max(body_color[2]-30,0)))
    else:
        d.rectangle([12, 12, 19, 24], fill=body_color)
        d.ellipse([11, 4, 20, 13], fill=body_color)
        d.point((13, 7), fill=eye_color); d.point((18, 7), fill=eye_color)
        d.rectangle([12, 24, 15, 30], fill=(max(body_color[0]-30,0), max(body_color[1]-30,0), max(body_color[2]-30,0)))
        d.rectangle([16, 24, 19, 30], fill=(max(body_color[0]-30,0), max(body_color[1]-30,0), max(body_color[2]-30,0)))
    if has_weapon:
        d.line([(24, 8), (24, 22)], fill=(160, 160, 170), width=2)

def goblin(d, i): creature(d, i, (80, 140, 50), (255, 255, 0), has_weapon=True)
def orc(d, i): creature(d, i, (140, 70, 50), (255, 60, 0), has_weapon=True)
def troll(d, i): creature(d, i, (100, 90, 70), (200, 180, 0), big=True)
def warg(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.ellipse([4, 10, 27, 26], fill=(120, 100, 70))
    d.ellipse([2, 8, 12, 16], fill=(130, 110, 75))  # head
    d.point((5, 11), fill=(255, 0, 0))
    # tail
    d.line([(26, 14), (30, 8)], fill=(110, 90, 60), width=2)
    # legs
    d.line([(10, 25), (10, 31)], fill=(100, 80, 55), width=2)
    d.line([(22, 25), (22, 31)], fill=(100, 80, 55), width=2)

def cave_spider(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.ellipse([10, 10, 21, 21], fill=(60, 60, 60))
    # legs
    for angle_x, angle_y in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        sx, sy = 15 + angle_x * 5, 15 + angle_y * 5
        d.line([(sx, sy), (sx + angle_x * 8, sy + angle_y * 8)], fill=(50, 50, 50), width=1)
    for angle_x in [-1, 1]:
        d.line([(15 + angle_x * 5, 15), (15 + angle_x * 10, 15)], fill=(50, 50, 50), width=1)
    d.point((13, 13), fill=(255, 0, 0)); d.point((18, 13), fill=(255, 0, 0))

def balrog(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 10, 0))
    d.rectangle([6, 6, 25, 28], fill=(180, 40, 0))
    d.ellipse([8, 1, 23, 10], fill=(200, 50, 0))
    d.point((12, 5), fill=(255, 255, 0)); d.point((19, 5), fill=(255, 255, 0))
    # fire aura
    for px, py in [(4, 8), (27, 8), (3, 20), (28, 20), (15, 0)]:
        d.point((px, py), fill=(255, 160, 0))
        if px > 0: d.point((px-1, py), fill=(255, 100, 0))
    # whip
    d.line([(26, 10), (31, 4)], fill=(255, 120, 0), width=1)
    d.line([(31, 4), (28, 0)], fill=(255, 80, 0), width=1)

def uruk_hai(d, i): creature(d, i, (130, 40, 40), (255, 100, 0), has_weapon=True, big=True)
def barrow_wight(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.rectangle([12, 10, 19, 26], fill=(160, 180, 200))
    d.ellipse([11, 3, 20, 12], fill=(180, 200, 220))
    d.point((13, 7), fill=(100, 200, 255)); d.point((18, 7), fill=(100, 200, 255))
    # ghostly trail
    for py in range(26, 31):
        d.point((14, py), fill=(140, 160, 180)); d.point((17, py), fill=(140, 160, 180))

def nazgul_shadow(d, i):
    d.rectangle([0, 0, 31, 31], fill=(10, 0, 15))
    d.rectangle([10, 8, 21, 28], fill=(30, 0, 50))
    d.ellipse([10, 2, 21, 11], fill=(40, 0, 60))
    d.point((13, 6), fill=(255, 0, 0)); d.point((18, 6), fill=(255, 0, 0))
    # cloak spread
    d.polygon([(10, 12), (3, 22), (10, 22)], fill=(25, 0, 40))
    d.polygon([(21, 12), (28, 22), (21, 22)], fill=(25, 0, 40))

def dragon_worm(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.ellipse([4, 8, 27, 24], fill=(180, 60, 20))
    d.ellipse([2, 6, 12, 14], fill=(200, 70, 25))
    d.point((5, 9), fill=(255, 255, 0))
    # fire breath
    d.point((0, 10), fill=(255, 200, 0))
    d.point((1, 9), fill=(255, 160, 0))


# ════════════════════════════════════════════════
# ITEMS
# ════════════════════════════════════════════════

def weapon(d, i, blade_color, handle_color=(120, 80, 40)):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.line([(15, 4), (15, 20)], fill=blade_color, width=2)
    d.line([(11, 20), (19, 20)], fill=handle_color, width=2)  # crossguard
    d.line([(15, 20), (15, 28)], fill=handle_color, width=2)  # grip

def item_sword(d, i): weapon(d, i, (200, 200, 210))
def item_axe(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.line([(15, 4), (15, 28)], fill=(120, 80, 40), width=2)
    d.polygon([(15, 6), (8, 12), (15, 14)], fill=(180, 180, 190))
def item_bow(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.arc([10, 4, 22, 28], 270, 90, fill=(130, 90, 45), width=2)
    d.line([(16, 4), (16, 28)], fill=(200, 190, 160), width=1)
def item_staff(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.line([(15, 2), (15, 30)], fill=(120, 80, 40), width=3)
    d.ellipse([12, 0, 18, 6], fill=(100, 160, 255))
def item_dagger(d, i): weapon(d, i, (190, 190, 200), (100, 70, 30))
def item_mace(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.line([(15, 12), (15, 28)], fill=(120, 80, 40), width=2)
    d.ellipse([10, 4, 20, 14], fill=(160, 160, 170))

def armor_piece(d, i, color, shape="rect"):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    if shape == "rect":
        d.rectangle([6, 4, 25, 27], fill=color, outline=(max(color[0]-40,0), max(color[1]-40,0), max(color[2]-40,0)))
    elif shape == "helmet":
        d.arc([6, 4, 25, 22], 0, 180, fill=color, width=3)
        d.rectangle([6, 13, 25, 22], fill=color)
        d.rectangle([10, 22, 21, 26], fill=(max(color[0]-20,0), max(color[1]-20,0), max(color[2]-20,0)))
    elif shape == "shield":
        d.polygon([(15, 4), (6, 10), (6, 22), (15, 28), (25, 22), (25, 10)], fill=color)
        d.polygon([(15, 8), (10, 12), (10, 20), (15, 24), (21, 20), (21, 12)], fill=(min(color[0]+30,255), min(color[1]+30,255), min(color[2]+30,255)))
    elif shape == "small":
        d.rectangle([8, 8, 23, 23], fill=color, outline=(max(color[0]-40,0), max(color[1]-40,0), max(color[2]-40,0)))

def item_leather_armor(d, i): armor_piece(d, i, (140, 100, 50))
def item_chainmail(d, i): armor_piece(d, i, (160, 160, 170))
def item_plate_armor(d, i): armor_piece(d, i, (190, 190, 200))
def item_helmet(d, i): armor_piece(d, i, (170, 170, 180), "helmet")
def item_shield(d, i): armor_piece(d, i, (140, 120, 80), "shield")
def item_gloves(d, i): armor_piece(d, i, (130, 100, 60), "small")
def item_boots(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.rectangle([6, 8, 14, 26], fill=(100, 70, 35))
    d.rectangle([17, 8, 25, 26], fill=(100, 70, 35))
    d.rectangle([4, 22, 14, 28], fill=(90, 60, 30))
    d.rectangle([17, 22, 27, 28], fill=(90, 60, 30))

# consumables
def item_bread(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.ellipse([5, 10, 26, 24], fill=(200, 170, 100))
    d.ellipse([7, 12, 24, 22], fill=(210, 180, 110))
    d.line([(12, 12), (12, 22)], fill=(180, 150, 80), width=1)

def item_meat(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.ellipse([6, 8, 22, 24], fill=(160, 60, 60))
    d.line([(22, 16), (28, 10)], fill=(200, 180, 140), width=3)  # bone

def item_lembas(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.rectangle([7, 9, 24, 22], fill=(230, 220, 170))
    # leaf wrapping
    d.polygon([(8, 10), (15, 6), (23, 10)], fill=(80, 140, 60))

def item_water_flask(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.ellipse([9, 10, 22, 26], fill=(60, 110, 180))
    d.rectangle([13, 6, 18, 12], fill=(80, 70, 50))  # cork

def item_ale(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.rectangle([10, 8, 21, 26], fill=(160, 120, 30))
    d.rectangle([10, 8, 21, 12], fill=(220, 200, 150))  # foam
    d.rectangle([8, 14, 10, 20], fill=(140, 100, 20))  # handle

def item_miruvor(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.ellipse([10, 12, 21, 26], fill=(180, 160, 220))
    d.rectangle([13, 6, 18, 14], fill=(200, 180, 240))
    d.point((15, 8), fill=(255, 255, 255))  # sparkle

def item_ent_draught(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.ellipse([9, 10, 22, 26], fill=(40, 140, 40))
    d.rectangle([12, 5, 19, 12], fill=(80, 60, 30))  # wooden container
    d.point((15, 18), fill=(100, 200, 100))

# magic items
def item_spell_parchment(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.rectangle([8, 4, 23, 27], fill=(220, 210, 180))
    # squiggly text lines
    for y in [9, 13, 17, 21]:
        d.line([(10, y), (21, y)], fill=(100, 60, 40), width=1)
    d.ellipse([12, 22, 19, 27], fill=(180, 100, 200))  # magic seal

def item_spell_book(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.rectangle([6, 4, 25, 27], fill=(80, 30, 120))
    d.rectangle([8, 6, 23, 25], fill=(100, 50, 150))
    d.rectangle([14, 10, 17, 20], fill=(200, 180, 80))  # clasp
    d.line([(6, 4), (6, 27)], fill=(60, 20, 90), width=2)  # spine

def item_amulet(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.arc([8, 2, 23, 14], 0, 180, fill=(200, 180, 60), width=1)  # chain
    d.ellipse([11, 12, 20, 24], fill=(180, 60, 60))
    d.ellipse([13, 14, 18, 22], fill=(220, 80, 80))
    d.point((15, 18), fill=(255, 200, 200))

def item_talisman(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.polygon([(15, 4), (8, 20), (15, 28), (23, 20)], fill=(60, 140, 120))
    d.polygon([(15, 8), (11, 18), (15, 24), (20, 18)], fill=(80, 180, 160))

def item_ring(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.ellipse([8, 8, 23, 23], fill=(200, 180, 60), outline=(180, 160, 40), width=1)
    d.ellipse([11, 11, 20, 20], fill=(30, 30, 35))
    d.ellipse([13, 8, 18, 13], fill=(100, 200, 255))  # gem

# misc
def item_torch(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.line([(15, 14), (15, 28)], fill=(120, 80, 40), width=3)
    d.ellipse([11, 4, 19, 15], fill=(255, 180, 40))
    d.ellipse([13, 2, 17, 8], fill=(255, 240, 100))

def item_key(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.ellipse([10, 4, 21, 14], fill=(200, 180, 60), outline=(180, 160, 40))
    d.ellipse([13, 6, 18, 11], fill=(30, 30, 35))
    d.line([(15, 14), (15, 26)], fill=(200, 180, 60), width=2)
    d.line([(15, 22), (19, 22)], fill=(200, 180, 60), width=1)
    d.line([(15, 26), (19, 26)], fill=(200, 180, 60), width=1)

def item_gold(d, i):
    d.rectangle([0, 0, 31, 31], fill=(30, 30, 35))
    d.ellipse([8, 10, 23, 22], fill=(220, 200, 50))
    d.ellipse([6, 12, 20, 24], fill=(200, 180, 40))
    d.ellipse([12, 8, 26, 20], fill=(240, 220, 60))

# UI icons
def ui_icon(d, i, color):
    d.rectangle([0, 0, 31, 31], fill=(20, 18, 25))
    d.ellipse([4, 4, 27, 27], fill=color)

def ui_heart(d, i):
    d.rectangle([0, 0, 31, 31], fill=(20, 18, 25))
    d.polygon([(15, 26), (4, 14), (4, 8), (10, 4), (15, 8), (21, 4), (27, 8), (27, 14)], fill=(200, 40, 40))

def ui_mana_orb(d, i): ui_icon(d, i, (40, 80, 200))


# ════════════════════════════════════════════════
# GENERATE ALL
# ════════════════════════════════════════════════

TEXTURES = {
    # Tiles
    "tiles/floor_stone.jpg": tile_floor_stone,
    "tiles/wall_stone.jpg": tile_wall_stone,
    "tiles/wall_mossy.jpg": tile_wall_mossy,
    "tiles/door_closed.jpg": tile_door_closed,
    "tiles/door_open.jpg": tile_door_open,
    "tiles/stairs_down.jpg": tile_stairs_down,
    "tiles/stairs_up.jpg": tile_stairs_up,
    "tiles/trap_hidden.jpg": tile_trap_hidden,
    "tiles/trap_revealed.jpg": tile_trap_revealed,
    "tiles/chest.jpg": tile_chest,
    "tiles/fountain.jpg": tile_fountain,
    "tiles/altar.jpg": tile_altar,
    # Player
    "player/warrior_idle.jpg": player_warrior,
    "player/mage_idle.jpg": player_mage,
    "player/ranger_idle.jpg": player_ranger,
    # Creatures
    "creatures/goblin.jpg": goblin,
    "creatures/orc.jpg": orc,
    "creatures/troll.jpg": troll,
    "creatures/warg.jpg": warg,
    "creatures/cave_spider.jpg": cave_spider,
    "creatures/balrog.jpg": balrog,
    "creatures/uruk_hai.jpg": uruk_hai,
    "creatures/barrow_wight.jpg": barrow_wight,
    "creatures/nazgul_shadow.jpg": nazgul_shadow,
    "creatures/dragon_worm.jpg": dragon_worm,
    # Weapons
    "items/weapons/sword.jpg": item_sword,
    "items/weapons/axe.jpg": item_axe,
    "items/weapons/bow.jpg": item_bow,
    "items/weapons/staff.jpg": item_staff,
    "items/weapons/dagger.jpg": item_dagger,
    "items/weapons/mace.jpg": item_mace,
    # Armor
    "items/armor/leather_armor.jpg": item_leather_armor,
    "items/armor/chainmail.jpg": item_chainmail,
    "items/armor/plate_armor.jpg": item_plate_armor,
    "items/armor/helmet.jpg": item_helmet,
    "items/armor/shield.jpg": item_shield,
    "items/armor/gloves.jpg": item_gloves,
    "items/armor/boots.jpg": item_boots,
    # Consumables
    "items/consumables/bread.jpg": item_bread,
    "items/consumables/meat.jpg": item_meat,
    "items/consumables/lembas.jpg": item_lembas,
    "items/consumables/water_flask.jpg": item_water_flask,
    "items/consumables/ale.jpg": item_ale,
    "items/consumables/miruvor.jpg": item_miruvor,
    "items/consumables/ent_draught.jpg": item_ent_draught,
    # Magic
    "items/magic/spell_parchment.jpg": item_spell_parchment,
    "items/magic/spell_book.jpg": item_spell_book,
    "items/magic/amulet.jpg": item_amulet,
    "items/magic/talisman.jpg": item_talisman,
    "items/magic/ring.jpg": item_ring,
    # Misc
    "items/misc/torch.jpg": item_torch,
    "items/misc/key.jpg": item_key,
    "items/misc/gold.jpg": item_gold,
    # UI
    "ui/heart.jpg": ui_heart,
    "ui/mana_orb.jpg": ui_mana_orb,
}


def main():
    count = 0
    for subpath, draw_fn in TEXTURES.items():
        make(subpath, draw_fn)
        count += 1
    print(f"Generated {count} textures in {BASE}/")


if __name__ == "__main__":
    main()
