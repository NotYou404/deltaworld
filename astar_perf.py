import random
import time

import arcade
import pyglet

PATH_UPDATE_INTERVAL = 0.6


def filter_border_walls(
    walls: arcade.SpriteList,
    border_width: float,
    border_height: float,
    map_width: float,
    map_height: float,
    start_x: float = 0,
    start_y: float = 0,
) -> arcade.SpriteList:
    """
    Filter walls segments making up the border out of a list of all wall
    segments, returning a new SpriteList without border segments.

    :param walls: A SpriteList of all wall segments.
    :type walls: arcade.SpriteList
    :param border_width: The width of the border in pixels.
    :type border_width: float
    :param border_height: The height of the border in pixels.
    :type border_height: float
    :param map_width: The map width in pixels
    :type map_width: float
    :param map_height: The map height in pixels
    :type map_height: float
    :param start_x: The pixel where the map starts on the X-Axis, defaults to 0
    :type start_x: float, optional
    :param start_y: The pixel where the map starts on the Y-Axis, defaults to 0
    :type start_y: float, optional
    :return: A new SpriteList without border segments.
    :rtype: arcade.SpriteList
    """
    new_list = arcade.SpriteList()
    boundaries_left = (start_x, start_x + border_width)
    boundaries_right = (map_width - border_width, map_width)
    boundaries_bottom = (start_y, start_y + border_height)
    boundaries_top = (map_height - border_height, map_height)
    for wall in walls:
        if not (
            wall.left >= boundaries_left[0]
            and wall.right <= boundaries_left[1]
            or wall.left >= boundaries_right[0]
            and wall.right <= boundaries_right[1]
            or wall.bottom >= boundaries_bottom[0]
            and wall.top <= boundaries_bottom[1]
            or wall.bottom >= boundaries_top[0]
            and wall.top <= boundaries_top[1]
        ):
            new_list.append(wall)
    return new_list


class Window(arcade.Window):
    def setup(self):
        self.text_batch = pyglet.graphics.Batch()
        self.map = arcade.tilemap.TileMap(
            "deltaworld/assets/maps/d1r3.tmj", use_spatial_hash=True,
        )
        self.scene = arcade.Scene.from_tilemap(self.map)
        self.scene.add_sprite_list("hostiles")
        self.fps_text = arcade.Text(
            "", x=400, y=500, font_size=24, batch=self.text_batch
        )
        self.walls_text = arcade.Text(
            "", x=400, y=450, font_size=24, batch=self.text_batch
        )
        self.hostiles_text = arcade.Text(
            "", x=400, y=400, font_size=24, batch=self.text_batch
        )
        self.perfs_text = arcade.Text(
            "", x=400, y=350, font_size=12, width=200,
            batch=self.text_batch, multiline=True,
        )

        arcade.schedule(self.add_hostile, interval=2)
        arcade.enable_timings()

        self.non_border_walls = filter_border_walls(
            self.scene["walls"],
            38,
            38,
            608,
            608,
        )

    def add_hostile(self, dt: float):
        self.scene.add_sprite("hostiles", sprite := arcade.Sprite(
            path_or_texture="deltaworld/assets/textures/hostiles/zombie/"
                            "zombie_default.png",
            center_x=random.randint(50, 458),
            center_y=random.randint(50, 458),
        ))
        sprite.last_path_update = 0
        sprite.path = []
        sprite.perfs = ()

    def on_update(self, delta_time: float):
        for hostile in self.scene["hostiles"]:
            if time.time() - hostile.last_path_update < PATH_UPDATE_INTERVAL:
                continue
            start = time.time()
            barrier_list = arcade.AStarBarrierList(
                hostile,
                self.non_border_walls,
                grid_size=38,
                left=0,
                right=608,
                bottom=0,
                top=608,
            )
            end_barr = time.time()
            path = arcade.astar_calculate_path(
                start_point=(hostile.center_x, hostile.center_y),
                end_point=(304, 304),
                astar_barrier_list=barrier_list,
                diagonal_movement=False,
            )
            end_path = time.time()
            hostile.path = path
            hostile.last_path_update = time.time()
            hostile.perfs = (start, end_barr, end_path)

        self.fps_text.text = f"{arcade.get_fps()} FPS"
        self.walls_text.text = f"{len(self.non_border_walls)} Walls"
        self.hostiles_text.text = f"{len(self.scene["hostiles"])} Hostiles"
        avg_barrier_list_time = round(sum(
            [x.perfs[1] - x.perfs[0] for x in self.scene["hostiles"]]
        ) / (len(self.scene["hostiles"]) or 1), 6)
        avg_astar_calc_time = round(sum(
            [x.perfs[2] - x.perfs[1] for x in self.scene["hostiles"]]
        ) / (len(self.scene["hostiles"]) or 1), 6)
        self.perfs_text.text = (
            "Average AStarBarrierList() instantiation time: "
            f"{avg_barrier_list_time}"
            "\nAverage astar_calc_path() time: "
            f"{avg_astar_calc_time}"
        )

    def on_draw(self):
        self.scene.draw()
        for hostile in self.scene["hostiles"]:
            arcade.draw_line_strip(
                hostile.path or [], color=arcade.csscolor.RED)
        self.text_batch.draw()


if __name__ == "__main__":
    win = Window(width=608, height=608, center_window=True)
    win.setup()
    arcade.run()
