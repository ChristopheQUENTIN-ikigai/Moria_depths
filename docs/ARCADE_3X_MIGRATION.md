# Arcade 3.x Migration Guide — Depths of Moria

This document records every Arcade 2.x → 3.x API breaking change encountered during development, the error messages produced, and the correct 3.x replacements.

## Summary of Issues Fixed

| # | Old API (2.x) | Error Message | Arcade 3.x Fix |
|---|--------------|---------------|-----------------|
| 1 | `arcade.draw_lrtb_rectangle_filled(l, r, t, b, color)` | `AttributeError: module 'arcade' has no attribute 'draw_lrtb_rectangle_filled'` | `arcade.draw_lrbt_rectangle_filled(l, r, b, t, color)` — note **argument order changed** from Left-Right-**Top**-Bottom to Left-Right-**Bottom**-Top |
| 2 | `arcade.draw_lrtb_rectangle_outline(...)` | Same pattern as above | `arcade.draw_lrbt_rectangle_outline(l, r, b, t, color, border_width)` |
| 3 | `texture.draw_scaled(cx, cy, scale)` | `AttributeError: 'Texture' object has no attribute 'draw_scaled'` | Use `arcade.Sprite(texture, scale=s)` inside an `arcade.SpriteList` — see Rendering section below |
| 4 | `sprite.draw()` | `AttributeError: 'Sprite' object has no attribute 'draw'` | Individual sprites cannot be drawn directly. Must use `SpriteList.draw()` |
| 5 | `arcade.draw_texture_rectangle(cx, cy, w, h, tex)` | `AttributeError` in some 3.x builds | Removed in arcade 3.x. Use Sprite + SpriteList pattern instead |

## Detailed Fix Descriptions

### 1. Rectangle Drawing — Argument Order Swap

**Arcade 2.x:**
```python
arcade.draw_lrtb_rectangle_filled(left, right, top, bottom, color)
```

**Arcade 3.x:**
```python
arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, color)
```

The function was renamed from `lrtb` (Left-Right-Top-Bottom) to `lrbt` (Left-Right-Bottom-Top). The parameter order follows the new name — `bottom` comes before `top`. This is a subtle change that compiles fine but draws rectangles in the wrong position if you just rename the function without swapping args.

**Files affected:** `views/game_view.py`, `views/game_over_view.py`, `ui/hud.py`

### 2. Texture Rendering — No More Direct Draw

**Arcade 2.x allowed:**
```python
texture = arcade.load_texture("file.jpg")
texture.draw_scaled(center_x, center_y, scale)
# or
arcade.draw_texture_rectangle(cx, cy, width, height, texture)
```

**Arcade 3.x requires SpriteList pattern:**
```python
texture = arcade.load_texture("file.jpg")
sprite = arcade.Sprite(texture, scale=desired_scale)
sprite.position = (center_x, center_y)

sprite_list = arcade.SpriteList()
sprite_list.append(sprite)
sprite_list.draw()  # Only SpriteList has .draw()
```

Individual `Sprite.draw()` no longer exists. All sprites must be collected into a `SpriteList` and drawn as a batch. This is actually better for performance since arcade 3.x batches all sprites in a list into a single GPU draw call.

**Our solution:** Rebuild two SpriteLists (`_visible_sprites`, `_explored_sprites`) after each turn in `_rebuild_sprite_lists()`, then just call `.draw()` on them each frame. This is both correct for the API and efficient.

### 3. Solid-Color Fallback Textures

When no texture file is available, we create a solid-color texture programmatically:

```python
tex = arcade.Texture.create_filled(
    f"solid_{r}_{g}_{b}",      # unique name for caching
    (TILE_SIZE, TILE_SIZE),     # size
    (r, g, b, 255)              # RGBA color
)
sprite = arcade.Sprite(tex)
```

`Texture.create_filled()` is new in arcade 3.x and very useful for procedural content.

### 4. Camera API

**Arcade 2.x:**
```python
camera = arcade.Camera(width, height)
camera.move_to((x, y))
camera.use()
```

**Arcade 3.x:**
```python
camera = arcade.camera.Camera2D()
camera.position = (center_x, center_y)
camera.use()
```

The camera module was reorganized under `arcade.camera`. The `Camera2D` class uses a `position` property instead of `move_to()`.

### 5. Window Initialization

**Arcade 3.x:**
```python
window = arcade.Window(width, height, title, resizable=True)
window.set_fullscreen(True)  # toggle at runtime
window.fullscreen             # bool property to check state
```

`resizable=True` is recommended so fullscreen toggle works smoothly.

### 6. Other API Notes

- `arcade.draw_line()` — unchanged, works the same in 3.x
- `arcade.draw_text()` — unchanged, works the same in 3.x
- `arcade.key.*` constants — unchanged
- `arcade.View` subclassing — unchanged
- `arcade.close_window()` — unchanged
- `arcade.run()` — unchanged

## Recommended Arcade 3.x Rendering Pattern

```python
class MyView(arcade.View):
    def __init__(self):
        super().__init__()
        self.sprite_list = arcade.SpriteList()

    def rebuild(self):
        """Call after game state changes."""
        self.sprite_list = arcade.SpriteList()
        for entity in entities:
            tex = arcade.load_texture(entity.image)
            sprite = arcade.Sprite(tex, scale=1.0)
            sprite.position = (entity.x, entity.y)
            self.sprite_list.append(sprite)

    def on_draw(self):
        self.clear()
        self.sprite_list.draw()  # single GPU batch call
```

This is the idiomatic arcade 3.x pattern: maintain SpriteLists, rebuild when state changes, draw the lists each frame.
