"""
GameView — main gameplay screen.
Arcade 3.x: SpriteList-based rendering, Camera2D, draw_lrbt_rectangle_filled.
"""
from __future__ import annotations
import os
import arcade
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, HALF_TILE,
    COLOR_BG, HUD_HEIGHT, HELP_TEXT,
    LAYER_FLOOR, LAYER_ITEM, LAYER_CREATURE, LAYER_PLAYER,
)
from ecs.world import World
from ecs.component import (
    Position, Renderable, Player, Health, FieldOfView,
    StairsDown, StairsUp, Inventory, Item, Blocker, Door,
    Fountain, Altar, SurvivalNeeds, Trap, Chest, Equipment,
    Equippable, Ammo,
)
from ecs.systems.movement_system import MovementSystem
from ecs.systems.combat_system import CombatSystem
from ecs.systems.ai_system import AISystem
from ecs.systems.fov_system import FOVSystem
from ecs.systems.inventory_system import InventorySystem
from ecs.systems.survival_system import SurvivalSystem
from ecs.systems.status_effect_system import StatusEffectSystem
from core.map_loader import load_level
from ui.hud import draw_hud

MAP_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "maps")
TEXTURE_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "textures")


class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.world: World | None = None
        self.camera: arcade.camera.Camera2D | None = None
        self.hud_camera: arcade.camera.Camera2D | None = None
        self.map_width = 0
        self.map_height = 0
        self._texture_cache: dict[str, arcade.Texture | None] = {}
        self._solid_cache: dict[tuple, arcade.Texture] = {}
        # Persistent per-layer sprite lists (never rebuilt from scratch each turn).
        self._sl: dict[int, arcade.SpriteList] = {}
        # eid → [sprite, layer, signature]; signature detects texture/color changes.
        self._sprites: dict[int, list] = {}
        self._show_help = False
        self._ranged_mode = False  # True when waiting for direction after R

    def _load_texture(self, path: str) -> arcade.Texture | None:
        if path in self._texture_cache:
            return self._texture_cache[path]
        full = os.path.join(TEXTURE_DIR, path) if not os.path.isabs(path) else path
        if os.path.exists(full):
            try:
                tex = arcade.load_texture(full)
                self._texture_cache[path] = tex
                return tex
            except Exception:
                pass
        self._texture_cache[path] = None
        return None

    def setup(self, depth: int = 1):
        self.world = World()
        self.world.current_depth = depth
        self.world.register_system(MovementSystem())
        self.world.register_system(CombatSystem())
        self.world.register_system(AISystem())
        self.world.register_system(InventorySystem())
        self.world.register_system(StatusEffectSystem())
        self.world.register_system(SurvivalSystem())
        self.world.register_system(FOVSystem())
        map_file = os.path.join(MAP_DIR, f"level_{depth:02d}.txt")
        self.map_width, self.map_height = load_level(self.world, map_file, depth)
        self.camera = arcade.camera.Camera2D()
        self.hud_camera = arcade.camera.Camera2D()
        self.world.player_intent = ("done",)
        FOVSystem().process(self.world)
        self._clear_sprites()
        self._sync_sprites()
        self.window.background_color = COLOR_BG

    def on_show_view(self):
        self.window.background_color = COLOR_BG

    # ── Persistent sprite management ─────────────────

    def _clear_sprites(self):
        """Drop all sprites (used on level load / depth change)."""
        self._sl = {}
        self._sprites = {}

    def _add_to_layer(self, sprite, layer):
        self._sl.setdefault(layer, arcade.SpriteList()).append(sprite)

    def _remove_sprite(self, eid):
        entry = self._sprites.pop(eid, None)
        if entry is None:
            return
        sprite, layer, _ = entry
        sl = self._sl.get(layer)
        if sl is not None:
            try:
                sl.remove(sprite)
            except ValueError:
                pass

    def _sync_sprites(self):
        """Reconcile sprites with the current world state without rebuilding.

        Sprites are created once and reused; per turn we only update positions,
        toggle visibility/alpha by FOV, and create/remove the few that changed."""
        if not self.world:
            return
        fov_r = self.world.player(Player, Position, FieldOfView)
        if not fov_r:
            return
        _, _, _p_pos, fov = fov_r
        depth = self.world.current_depth
        vis = fov.visible_tiles
        expl = fov.explored_tiles
        present = set()
        for eid, pos, rend in self.world.query(Position, Renderable):
            if pos.depth != depth:
                continue
            present.add(eid)
            tk = (pos.x, pos.y)
            visible = tk in vis
            show = visible or (rend.layer == LAYER_FLOOR and tk in expl)
            entry = self._sprites.get(eid)
            if not show:
                if entry is not None:
                    entry[0].visible = False
                continue
            sig = (rend.texture_path, tuple(rend.color))
            if entry is None or entry[2] != sig or entry[1] != rend.layer:
                if entry is not None:
                    self._remove_sprite(eid)
                px = pos.x * TILE_SIZE + HALF_TILE
                py = pos.y * TILE_SIZE + HALF_TILE
                sprite = self._make_sprite(rend, px, py)
                self._add_to_layer(sprite, rend.layer)
                self._sprites[eid] = [sprite, rend.layer, sig]
            else:
                sprite = entry[0]
            sprite.position = (pos.x * TILE_SIZE + HALF_TILE,
                               pos.y * TILE_SIZE + HALF_TILE)
            sprite.visible = True
            sprite.alpha = 255 if visible else 80
        # Remove sprites for entities that left this depth or were destroyed.
        for eid in [e for e in self._sprites if e not in present]:
            self._remove_sprite(eid)

    def _solid_texture(self, r: int, g: int, b: int) -> arcade.Texture:
        key = (r, g, b)
        tex = self._solid_cache.get(key)
        if tex is None:
            # Arcade 3.x removed Texture.create_filled; create_empty fills with the given color.
            tex = arcade.Texture.create_empty(f"s_{r}_{g}_{b}", (TILE_SIZE, TILE_SIZE), (r, g, b, 255))
            self._solid_cache[key] = tex
        return tex

    def _make_sprite(self, rend, cx, cy):
        tex = self._load_texture(rend.texture_path) if rend.texture_path else None
        if tex:
            scale = TILE_SIZE / max(tex.width, tex.height, 1)
            sprite = arcade.Sprite(tex, scale=scale)
        else:
            r, g, b = rend.color[:3]
            sprite = arcade.Sprite(self._solid_texture(r, g, b))
        sprite.position = (cx, cy)
        return sprite

    # ── Rendering ────────────────────────────────────

    def on_draw(self):
        self.clear()
        if not self.world:
            return
        fov_r = self.world.player(Player, Position, FieldOfView)
        if not fov_r:
            return
        _, _, p_pos, fov = fov_r
        self.camera.position = (
            p_pos.x * TILE_SIZE + HALF_TILE,
            p_pos.y * TILE_SIZE + HALF_TILE + HUD_HEIGHT // 2,
        )
        self.camera.use()
        for layer in sorted(self._sl):
            self._sl[layer].draw()

        self.hud_camera.use()
        draw_hud(self.world)

        if self._ranged_mode:
            arcade.draw_text(
                "RANGED: Press Arrow key to shoot (ESC to cancel)",
                SCREEN_WIDTH // 2, HUD_HEIGHT + 10, (255, 200, 50), 14,
                anchor_x="center",
            )
        if self._show_help:
            self._draw_help()

    def _draw_help(self):
        # Semi-transparent overlay
        arcade.draw_lrbt_rectangle_filled(
            60, SCREEN_WIDTH - 60, 40, SCREEN_HEIGHT - 40,
            (10, 10, 15, 230),
        )
        arcade.draw_text(
            "=== HELP — Key Bindings ===",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 70,
            (200, 180, 120), 20, anchor_x="center", bold=True,
        )
        y = SCREEN_HEIGHT - 110
        for section_name, bindings in HELP_TEXT:
            arcade.draw_text(section_name, 100, y, (180, 160, 100), 14, bold=True)
            y -= 22
            for key_str, desc in bindings:
                arcade.draw_text(f"  {key_str:20s} {desc}", 100, y, (180, 180, 180), 12)
                y -= 18
            y -= 8
        # Drinking water tip
        arcade.draw_text(
            "TIP: To drink water, press I (inventory), select Water Flask, press U (use).",
            100, y, (100, 180, 220), 12,
        )
        y -= 18
        arcade.draw_text(
            "TIP: To switch weapons, press I, select a weapon, press E (equip). Old weapon returns to pack.",
            100, y, (100, 180, 220), 12,
        )
        y -= 28
        arcade.draw_text(
            "Press H to close", SCREEN_WIDTH // 2, y, (150, 150, 160), 12, anchor_x="center",
        )

    # ── Input handling ───────────────────────────────

    def on_key_press(self, key, modifiers):
        if not self.world:
            return

        # ── Toggle help (always works) ──
        if key == arcade.key.H:
            self._show_help = not self._show_help
            return

        # ── Fullscreen toggle ──
        if key == arcade.key.F:
            self.window.set_fullscreen(not self.window.fullscreen)
            return

        # ── Escape ──
        if key == arcade.key.ESCAPE:
            if self._ranged_mode:
                self._ranged_mode = False
                self.world.log("Cancelled ranged attack.", (150, 150, 150))
                return
            if self._show_help:
                self._show_help = False
                return
            from views.title_view import TitleView
            self.window.show_view(TitleView())
            return

        # Don't process gameplay while help is open
        if self._show_help:
            return

        # Check alive
        pr = self.world.query_single(Player, Health)
        if pr:
            _, _, p_hp = pr
            if not p_hp.alive:
                from views.game_over_view import GameOverView
                self.window.show_view(GameOverView(self.world))
                return

        handled = False

        # ── Ranged mode: waiting for direction ──
        if self._ranged_mode:
            dx, dy = 0, 0
            if key == arcade.key.UP:
                dx, dy = 0, 1
            elif key == arcade.key.DOWN:
                dx, dy = 0, -1
            elif key == arcade.key.LEFT:
                dx, dy = -1, 0
            elif key == arcade.key.RIGHT:
                dx, dy = 1, 0
            else:
                return
            self._ranged_mode = False
            self.world.player_intent = ("ranged_attack", dx, dy)
            handled = True

        # ── Normal keys ──
        elif key == arcade.key.UP:
            self.world.player_intent = ("move", 0, 1); handled = True
        elif key == arcade.key.DOWN:
            self.world.player_intent = ("move", 0, -1); handled = True
        elif key == arcade.key.LEFT:
            self.world.player_intent = ("move", -1, 0); handled = True
        elif key == arcade.key.RIGHT:
            self.world.player_intent = ("move", 1, 0); handled = True

        elif key == arcade.key.PERIOD and (modifiers & arcade.key.MOD_SHIFT):
            self._use_stairs(StairsDown); handled = True
        elif key == arcade.key.COMMA and (modifiers & arcade.key.MOD_SHIFT):
            self._use_stairs(StairsUp); handled = True

        elif key == arcade.key.G:
            self._pickup_item(); handled = True

        elif key == arcade.key.I:
            from views.inventory_view import InventoryView
            self.window.show_view(InventoryView(self.world, self))
            return
        elif key == arcade.key.C:
            from views.character_view import CharacterView
            self.window.show_view(CharacterView(self.world, self))
            return

        elif key == arcade.key.E:
            self._interact(); handled = True

        elif key == arcade.key.R:
            # Enter ranged mode
            self._start_ranged()
            return

        elif key == arcade.key.SPACE:
            self.world.player_intent = ("done",); handled = True

        if handled:
            self.world.process_turn()
            self._sync_sprites()
            pr = self.world.query_single(Player, Health)
            if pr:
                _, _, p_hp = pr
                if not p_hp.alive:
                    from views.game_over_view import GameOverView
                    self.window.show_view(GameOverView(self.world))

    # ── Ranged attack start ──────────────────────────

    def _start_ranged(self):
        pr = self.world.query_single(Player, Equipment, Inventory)
        if not pr:
            return
        _, _, equip, inv = pr
        if equip.weapon is None:
            self.world.log("No weapon equipped.", (180, 180, 180))
            return
        weap = self.world.get(equip.weapon, Equippable)
        if not weap or not weap.ranged:
            self.world.log("Equip a ranged weapon first (bow/crossbow via Inventory).", (180, 180, 180))
            return
        # Check ammo
        has_ammo = False
        for eid in inv.items:
            a = self.world.get(eid, Ammo)
            if a and a.ammo_type == weap.ammo_type:
                has_ammo = True
                break
        if not has_ammo:
            self.world.log(f"No {weap.ammo_type}s! Find some on the map.", (200, 100, 100))
            return
        self._ranged_mode = True
        self.world.log("Ranged mode: press Arrow key to shoot.", (255, 200, 50))

    # ── Helpers ──────────────────────────────────────

    def _use_stairs(self, stair_type):
        p = self.world.query_single(Player, Position)
        if not p:
            return
        _, _, p_pos = p
        for eid in self.world.get_entities_at(p_pos.x, p_pos.y, p_pos.depth):
            stair = self.world.get(eid, stair_type)
            if stair:
                new_depth = stair.target_depth
                map_file = os.path.join(MAP_DIR, f"level_{new_depth:02d}.txt")
                if not os.path.exists(map_file):
                    self.world.log("There's nothing beyond here...", (180, 180, 180))
                    return
                direction = "descend" if stair_type == StairsDown else "ascend"
                self.world.log(f"You {direction} to depth {new_depth}.", (200, 180, 120))
                self._change_depth(new_depth)
                return
        self.world.log("No stairs here.", (180, 180, 180))

    def _change_depth(self, new_depth):
        pr = self.world.query_single(Player, Inventory)
        keep = set()
        if pr:
            p_eid, _, inv = pr
            keep.add(p_eid)
            keep.update(inv.items)
            from ecs.component import Equipment
            eq = self.world.get(p_eid, Equipment)
            if eq:
                keep.update(eq.get_all_equipped())
        for eid in list(self.world._components.keys()):
            if eid not in keep:
                self.world.destroy_entity(eid)
        self.world.current_depth = new_depth
        mf = os.path.join(MAP_DIR, f"level_{new_depth:02d}.txt")
        self.map_width, self.map_height = load_level(self.world, mf, new_depth)
        ppr = self.world.query_single(Player, Position)
        if ppr:
            p_eid2, _, pp = ppr
            tx, ty = pp.x, pp.y
            for eid, sup, sp in self.world.query(StairsUp, Position):
                if sp.depth == new_depth:
                    tx, ty = sp.x, sp.y
                    break
            self.world.move_entity(p_eid2, tx, ty, new_depth)
        fr = self.world.query_single(Player, FieldOfView)
        if fr:
            _, _, fov = fr
            fov.visible_tiles.clear()
            fov.explored_tiles.clear()
        FOVSystem().process(self.world)
        self._clear_sprites()
        self._sync_sprites()

    def _pickup_item(self):
        p = self.world.query_single(Player, Position, Inventory)
        if not p:
            return
        p_eid, _, p_pos, inv = p
        for eid in self.world.get_entities_at(p_pos.x, p_pos.y, p_pos.depth):
            if eid == p_eid:
                continue
            item = self.world.get(eid, Item)
            if item:
                self.world.player_intent = ("pickup", eid)
                return
        self.world.log("Nothing to pick up here.", (150, 150, 150))
        self.world.player_intent = ("done",)

    def _interact(self):
        p = self.world.query_single(Player, Position, Health, SurvivalNeeds)
        if not p:
            return
        p_eid, _, p_pos, p_hp, needs = p
        for eid in self.world.get_entities_at(p_pos.x, p_pos.y, p_pos.depth):
            fountain = self.world.get(eid, Fountain)
            if fountain and fountain.uses_left > 0:
                fountain.uses_left -= 1
                needs.thirst = min(100.0, needs.thirst + 40.0)
                p_hp.current = min(p_hp.maximum, p_hp.current + 10)
                self.world.log(f"You drink from the fountain. ({fountain.uses_left} uses left)", (80, 140, 220))
                self.world.player_intent = ("done",)
                return
            altar = self.world.get(eid, Altar)
            if altar and not altar.used_this_visit:
                altar.used_this_visit = True
                needs.willpower = min(100.0, needs.willpower + 30.0)
                needs.stress = max(0.0, needs.stress - 20.0)
                needs.sleep = min(100.0, needs.sleep + 20.0)
                self.world.log("You pray at the altar. Peace fills your mind.", (220, 220, 180))
                self.world.player_intent = ("done",)
                return
            chest = self.world.get(eid, Chest)
            if chest and not chest.opened:
                chest.opened = True
                from core.map_loader import _spawn_random_item
                _spawn_random_item(self.world, p_pos.x, p_pos.y, p_pos.depth)
                self.world.log("You open the chest and find something!", (210, 170, 60))
                self.world.player_intent = ("done",)
                return
        self.world.log("Nothing to interact with here.", (150, 150, 150))
        self.world.player_intent = ("done",)
