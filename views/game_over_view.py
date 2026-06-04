"""
GameOverView — displayed when the player dies.
"""
from __future__ import annotations
import arcade
from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from ecs.world import World
from ecs.component import Player, Experience


class GameOverView(arcade.View):
    def __init__(self, world: World):
        super().__init__()
        self.world = world

    def on_show_view(self):
        self.window.background_color = (10, 0, 0)

    def on_draw(self):
        self.clear()
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        arcade.draw_text(
            "YOU  HAVE  PERISHED",
            cx, cy + 80, (200, 40, 40), 36,
            anchor_x="center", anchor_y="center",
            font_name="Courier New", bold=True,
        )
        arcade.draw_text(
            "The darkness of Moria claims another soul...",
            cx, cy + 30, (150, 120, 100), 16,
            anchor_x="center", anchor_y="center",
        )

        result = self.world.query_single(Player, Experience)
        if result:
            _, _, xp = result
            arcade.draw_text(
                f"Level {xp.level}  |  Depth {self.world.current_depth}  |  Turn {self.world.turn}",
                cx, cy - 30, (180, 180, 180), 14,
                anchor_x="center", anchor_y="center",
            )

        arcade.draw_text(
            "[ N ] New Game     [ Q ] Quit",
            cx, cy - 100, (180, 200, 220), 18,
            anchor_x="center", anchor_y="center",
        )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.N:
            from views.game_view import GameView
            gv = GameView()
            gv.setup()
            self.window.show_view(gv)
        elif key == arcade.key.Q:
            arcade.close_window()
