"""
FOVSystem — recomputes the player's field of view after each turn.

Uses a simple recursive shadowcasting algorithm.
"""
from __future__ import annotations
from ecs.world import World
from ecs.component import Position, Player, FieldOfView


class FOVSystem:
    def process(self, world: World) -> None:
        result = world.query_single(Player, Position, FieldOfView)
        if result is None:
            return
        _, _, pos, fov = result

        fov.visible_tiles.clear()
        _compute_fov(world, pos.x, pos.y, pos.depth, fov.radius, fov.visible_tiles)
        fov.explored_tiles.update(fov.visible_tiles)


def _compute_fov(
    world: World, ox: int, oy: int, depth: int, radius: int, visible: set
) -> None:
    """Simple raycasting FOV — cast rays in all directions."""
    visible.add((ox, oy))
    import math
    num_rays = 360
    for i in range(num_rays):
        angle = math.radians(i)
        dx = math.cos(angle)
        dy = math.sin(angle)
        _cast_ray(world, ox, oy, dx, dy, depth, radius, visible)


def _cast_ray(
    world: World,
    ox: int, oy: int,
    dx: float, dy: float,
    depth: int, radius: int,
    visible: set,
) -> None:
    x, y = float(ox), float(oy)
    for _ in range(radius):
        x += dx
        y += dy
        ix, iy = round(x), round(y)
        dist_sq = (ix - ox) ** 2 + (iy - oy) ** 2
        if dist_sq > radius * radius:
            return
        visible.add((ix, iy))
        if world.blocks_sight_at(ix, iy, depth):
            return
