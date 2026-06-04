#!/usr/bin/env python3
"""
Depths of Moria — main entry point.
Run:  python main.py
Requirements:  pip install arcade>=3.0
"""
import arcade
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE
from views.title_view import TitleView


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)
    window.show_view(TitleView())
    arcade.run()


if __name__ == "__main__":
    main()
