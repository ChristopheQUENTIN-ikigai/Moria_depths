"""TitleView — Main menu (game + content editors)."""
from __future__ import annotations
import arcade
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG


class TitleView(arcade.View):
    def on_show_view(self):
        self.window.background_color = COLOR_BG

    def on_draw(self):
        self.clear()
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        arcade.draw_text("DEPTHS  OF  MORIA", cx, cy + 200, (200, 170, 100), 42,
                         anchor_x="center", anchor_y="center", font_name="Courier New", bold=True)
        arcade.draw_text("A Roguelike Dungeon Crawler", cx, cy + 152, (150, 140, 120), 16,
                         anchor_x="center", anchor_y="center")

        arcade.draw_text("[ N ]  New Game", cx, cy + 80, (180, 200, 220), 20,
                         anchor_x="center", anchor_y="center", font_name="Courier New")
        arcade.draw_text("[ F ]  Toggle Fullscreen", cx, cy + 46, (180, 200, 220), 20,
                         anchor_x="center", anchor_y="center", font_name="Courier New")
        arcade.draw_text("[ ESC / Q ]  Quit", cx, cy + 12, (180, 200, 220), 20,
                         anchor_x="center", anchor_y="center", font_name="Courier New")

        arcade.draw_text("— Content Editors —", cx, cy - 44, (150, 130, 100), 15,
                         anchor_x="center", anchor_y="center", font_name="Courier New")
        arcade.draw_text("[ I ]  Items        [ M ]  Monsters", cx, cy - 80, (170, 190, 170), 18,
                         anchor_x="center", anchor_y="center", font_name="Courier New")
        arcade.draw_text("[ W ]  Weapons & Armor   [ S ]  Spells", cx, cy - 112, (170, 190, 170), 18,
                         anchor_x="center", anchor_y="center", font_name="Courier New")

        arcade.draw_text("Press H in-game for full key bindings", cx, cy - 180,
                         (120, 120, 130), 12, anchor_x="center", anchor_y="center")

    def _open_editor(self, kind):
        from views.editor_view import EditorView, EDITORS
        self.window.show_view(EditorView(EDITORS[kind]()))

    def on_key_press(self, key, modifiers):
        if key == arcade.key.N:
            from views.game_view import GameView
            gv = GameView()
            gv.setup()
            self.window.show_view(gv)
        elif key == arcade.key.F:
            self.window.set_fullscreen(not self.window.fullscreen)
        elif key == arcade.key.I:
            self._open_editor("item")
        elif key == arcade.key.M:
            self._open_editor("creature")
        elif key == arcade.key.W:
            self._open_editor("equipment")
        elif key == arcade.key.S:
            self._open_editor("spell")
        elif key in (arcade.key.Q, arcade.key.ESCAPE):
            arcade.close_window()
