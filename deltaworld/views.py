from typing import TYPE_CHECKING

import cme.concurrency
import cme.localization
import cme.sound
import cme.text
import cme.view
from cme import csscolor, key
from cme.camera import Camera
from cme.shapes import Batch, Rectangle, draw_xywh_rectangle_filled
from cme.sprite import (AnimatedSprite, Scene, Sprite, SpriteList,
                        check_for_collision, check_for_collision_with_list)
from cme.text import center_x, center_y
from cme.texture import (PymunkHitBoxAlgorithm, Texture, load_texture,
                         load_texture_series)

from .enums import Font
from .model import Player
from .paths import MAPS_PATH, MUSIC_PATH, TEXTURES_PATH

if TYPE_CHECKING:
    from .window import Window


MAP_SIZE = 608


class MenuView(cme.view.FadingView):
    """
    View handling the main menu where the user can start the actual gameplay,
    change settings and quit.
    """
    window: "Window"

    def setup(self) -> None:
        self.pixel_sprites = SpriteList()
        self.text_batch = Batch()
        self.settings_batch = Batch()

        self.header = cme.text.Text(
            text="",
            start_x=0,
            start_y=0,
            color=csscolor.WHITE,
            font_size=72,
            font_name=Font.november,
            batch=self.text_batch
        )
        self.start_game = cme.text.Text(
            text="",
            start_x=0,
            start_y=0,
            color=csscolor.WHITE,
            font_size=24,
            font_name=Font.november,
            batch=self.text_batch
        )
        self.settings = cme.text.Text(
            text="",
            start_x=0,
            start_y=0,
            color=csscolor.WHITE,
            font_size=24,
            font_name=Font.november,
            batch=self.text_batch
        )
        self.quit = cme.text.Text(
            text="",
            start_x=0,
            start_y=0,
            color=csscolor.WHITE,
            font_size=24,
            font_name=Font.november,
            batch=self.text_batch
        )
        self.selected_item = self.start_game

        void = Texture.create_empty("void", size=(1, 1))
        self.pointer_right = AnimatedSprite(scale=5)
        self.pointer_right.add_texture(load_texture(
            TEXTURES_PATH / "pointer_right.png",
        ), "blinking")
        self.pointer_right.add_texture(void, "blinking")
        self.pointer_right.state = "blinking"
        self.pointer_right.animation_speed = 0.6
        self.pointer_left = AnimatedSprite(scale=5)
        self.pointer_left.add_texture(load_texture(
            TEXTURES_PATH / "pointer_left.png",
        ), "blinking")
        self.pointer_left.add_texture(void, "blinking")
        self.pointer_left.state = "blinking"
        self.pointer_left.animation_speed = 0.6
        self.pixel_sprites.extend([self.pointer_right, self.pointer_left])

        self.create_settings_menu()
        self.hide_settings_menu()
        self.apply_language()

    def on_resize(self, width: int, height: int) -> None:
        center_x(self.header, width)
        self.header.y = height / 1.4
        center_x(self.start_game, width)
        self.start_game.y = height / 2.4
        center_x(self.settings, width)
        self.settings.y = self.start_game.y - 50
        center_x(self.quit, width)
        self.quit.y = self.settings.y - 50

        self.pointer_right.center_x = self.selected_item.left - 40
        self.pointer_right.center_y = self.selected_item.y + self.selected_item.content_height / 2  # noqa
        self.pointer_left.center_x = self.selected_item.right + 40
        self.pointer_left.center_y = self.selected_item.y + self.selected_item.content_height / 2  # noqa

        self.settings_menu.center_x = self.window.width / 2
        self.settings_menu.center_y = self.window.height / 2
        center_x(self.settings_menu_header, width)
        self.settings_menu_header.y = self.settings_menu.top - 90
        center_x(self.settings_tooltip, width)
        self.settings_tooltip.y = self.settings_menu_header.y - 50
        center_x(self.settings_lang_label, width)
        self.settings_lang_label.y = self.settings_tooltip.y - 60
        center_x(self.settings_lang_switch, width)
        self.settings_lang_switch.y = self.settings_lang_label.y - 40
        center_x(self.settings_volume_label, width)
        self.settings_volume_label.y = self.settings_lang_switch.y - 60
        center_x(self.settings_volume_switch, width)
        self.settings_volume_switch.y = self.settings_volume_label.y - 40
        center_x(self.settings_controls_label, width)
        self.settings_controls_label.y = self.settings_volume_label.y - 100

        item_above = self.settings_controls_label
        for control in self.settings_controls:
            center_x(control, width)
            control.y = item_above.y - 40
            item_above = control

        center_x(self.settings_back, width)
        self.settings_back.y = item_above.y - 80

        self.settings_pointer_right.center_x = self.selected_setting.left - 40
        self.settings_pointer_right.center_y = self.selected_setting.y + self.selected_setting.content_height / 2  # noqa
        self.settings_pointer_left.center_x = self.selected_setting.right + 40
        self.settings_pointer_left.center_y = self.selected_setting.y + self.selected_setting.content_height / 2  # noqa

        self.rebind_overlay.width = width
        self.rebind_overlay.height = height
        center_x(self.rebind_text, width)
        center_y(self.rebind_text, height)

    def on_key_press(self, symbol: int, modifiers: int):
        super().on_key_press(symbol, modifiers)
        if self.rebind_overlay.visible:
            # Rebinding controls
            setattr(
                self.window.settings.controls,
                self.selected_setting.control,
                symbol,
            )
            self.rebind_overlay.visible = False
            self.apply_language()
            self.on_resize(self.window.width, self.window.height)
            return

        if symbol == key.UP:
            if not self.settings_menu.visible:
                if self.selected_item == self.settings:
                    self.selected_item = self.start_game
                elif self.selected_item == self.quit:
                    self.selected_item = self.settings
            else:
                idx = self.settings_actions.index(self.selected_setting)
                if idx != 0:
                    self.selected_setting = self.settings_actions[idx - 1]
            self.on_resize(self.window.width, self.window.height)
        elif symbol == key.DOWN:
            if not self.settings_menu.visible:
                if self.selected_item == self.start_game:
                    self.selected_item = self.settings
                elif self.selected_item == self.settings:
                    self.selected_item = self.quit
            else:
                idx = self.settings_actions.index(self.selected_setting)
                if idx != len(self.settings_actions) - 1:
                    self.selected_setting = self.settings_actions[idx + 1]
            self.on_resize(self.window.width, self.window.height)
        elif symbol == key.ENTER:
            if not self.settings_menu.visible:
                if self.selected_item == self.start_game:
                    self.next_view = GameView
                    self.start_fade_out()
                elif self.selected_item == self.settings:
                    self.show_settings_menu()
                else:
                    self.window.close()
            else:
                if self.selected_setting == self.settings_back:
                    self.hide_settings_menu()
                elif self.selected_setting not in (
                    self.settings_lang_switch,
                    self.settings_volume_switch,
                ):  # Control rebind
                    self.rebind_overlay.visible = True

        elif symbol in (key.LEFT, key.RIGHT):
            if not self.settings_menu.visible:
                pass
            else:
                if self.selected_setting == self.settings_lang_switch:
                    codes = cme.localization.LangDict.get_available_langcodes()
                    idx = codes.index(self.window.lang.langcode)
                    if symbol == key.LEFT:
                        next_code = codes[idx - 1]
                    else:
                        try:
                            next_code = codes[idx + 1]
                        except IndexError:
                            next_code = codes[0]
                    self.window.settings.langcode = next_code
                    self.window.settings.apply(self.window)
                    self.apply_language()
                    self.settings_lang_switch.text = self.window.lang.name
                    self.on_resize(self.window.width, self.window.height)
                elif self.selected_setting == self.settings_volume_switch:
                    if symbol == key.LEFT:
                        self.window.settings.volume -= 0.02
                    else:
                        self.window.settings.volume += 0.02
                    self.window.settings.apply(self.window)
                    self.settings_volume_switch.text = str(int(self.window.settings.volume * 100))  # noqa
                    self.on_resize(self.window.width, self.window.height)
                else:  # Controls
                    pass  # Controls only react on Enter

    def apply_language(self):
        self.header.text = self.window.lang["deltaworld"]
        self.start_game.text = self.window.lang["start_game"]
        self.settings.text = self.window.lang["options"]
        self.quit.text = self.window.lang["quit"]
        self.settings_menu_header.text = self.window.lang["options_menu"]
        self.settings_tooltip.text = self.window.lang["use_arrows_to_switch_value"]  # noqa
        self.settings_lang_label.text = self.window.lang["language"]
        self.settings_volume_label.text = self.window.lang["volume"]
        self.settings_controls_label.text = self.window.lang["controls"]
        for control in self.settings_controls:
            control_id = getattr(
                self.window.settings.controls, control.control
            )
            control_name = key.reverse_lookup.get(
                control_id, f"<{control_id}>"
            )
            control.text = self.window.lang[control.control].format(
                key=control_name
            )
        self.settings_back.text = self.window.lang["back"]
        self.rebind_text.text = self.window.lang["press_any_key_to_rebind"]

    def create_settings_menu(self):
        self.settings_entries = []

        self.settings_menu = Sprite(
            path_or_texture=load_texture(
                TEXTURES_PATH / "menus" / "settings.png"
            ),
            scale=25,
        )
        self.settings_pointer_right = Sprite(
            path_or_texture=load_texture(
                TEXTURES_PATH / "pointer_right.png",
            ),
            scale=4,
        )
        self.settings_pointer_left = Sprite(
            path_or_texture=load_texture(
                TEXTURES_PATH / "pointer_left.png",
            ),
            scale=4,
        )
        self.pixel_sprites.extend([
            self.settings_pointer_right, self.settings_pointer_left
        ])

        self.settings_menu_header = cme.text.Text(
            text="",
            start_x=0,
            start_y=0,
            color=csscolor.WHITE,
            font_size=32,
            font_name=Font.november,
            batch=self.settings_batch,
        )
        self.settings_tooltip = cme.text.Text(
            text="",
            start_x=0,
            start_y=0,
            color=csscolor.WHITE,
            font_size=18,
            font_name=Font.november,
            batch=self.settings_batch,
        )
        self.settings_lang_label = cme.text.Text(
            text="",
            start_x=0,
            start_y=0,
            color=csscolor.WHITE,
            font_size=18,
            font_name=Font.november,
            batch=self.settings_batch,
        )
        self.settings_lang_switch = cme.text.Text(
            text=self.window.lang.name,
            start_x=0,
            start_y=0,
            color=csscolor.WHITE,
            font_size=18,
            font_name=Font.november,
            batch=self.settings_batch,
        )
        self.selected_setting = self.settings_lang_switch
        self.settings_volume_label = cme.text.Text(
            text="",
            start_x=0,
            start_y=0,
            color=csscolor.WHITE,
            font_size=18,
            font_name=Font.november,
            batch=self.settings_batch,
        )
        self.settings_volume_switch = cme.text.Text(
            text=str(int(self.window.settings.volume * 100)),
            start_x=0,
            start_y=0,
            color=csscolor.WHITE,
            font_size=18,
            font_name=Font.november,
            batch=self.settings_batch,
        )
        self.settings_controls_label = cme.text.Text(
            text=self.window.lang["controls"],
            start_x=0,
            start_y=0,
            color=csscolor.WHITE,
            font_size=26,
            font_name=Font.november,
            batch=self.settings_batch,
        )

        self.settings_controls = []
        for control in ("move_up", "move_down", "move_left", "move_right",
                        "shoot_up", "shoot_down", "shoot_left", "shoot_right",
                        "use_item"):
            self.settings_controls.append(
                obj := cme.text.Text(
                    text="",
                    start_x=0,
                    start_y=0,
                    color=csscolor.WHITE,
                    font_size=18,
                    font_name=Font.november,
                    batch=self.settings_batch,
                )
            )
            obj.control = control

        self.settings_back = cme.text.Text(
            text="",
            start_x=0,
            start_y=0,
            color=csscolor.WHITE,
            font_size=18,
            font_name=Font.november,
            batch=self.settings_batch,
        )

        self.settings_actions = [
            self.settings_lang_switch,
            self.settings_volume_switch,
            *self.settings_controls,
            self.settings_back,
        ]

        self.pixel_sprites.append(self.settings_menu)
        self.settings_entries.extend([
            self.settings_menu_header, self.settings_tooltip,
            self.settings_lang_label, self.settings_lang_switch,
            self.settings_volume_label, self.settings_volume_switch,
            self.settings_controls_label, self.settings_back,
        ])
        self.settings_entries.extend(self.settings_controls)

        self.rebind_overlay = Rectangle(
            x=0,
            y=0,
            width=0,
            height=0,
            color=cme.types.Color(0, 0, 0, 200),
        )
        self.rebind_overlay.visible = False
        self.rebind_text = cme.text.Text(
            text="",
            start_x=0,
            start_y=0,
            color=csscolor.WHITE,
            font_size=36,
            font_name=Font.november,
        )

        self.on_resize(self.window.width, self.window.height)

    def show_settings_menu(self):
        self.settings_menu.visible = True
        self.settings_pointer_right.visible = True
        self.settings_pointer_left.visible = True
        self.selected_setting = self.settings_lang_switch
        self.on_resize(self.window.width, self.window.height)

    def hide_settings_menu(self):
        self.settings_menu.visible = False
        self.settings_pointer_right.visible = False
        self.settings_pointer_left.visible = False

    def on_show_view(self) -> None:
        super().on_show_view()
        self.window.background_color = csscolor.BLACK
        self.start_fade_in()

        background_music_source = cme.sound.load_sound(
            MUSIC_PATH / "crystal_cave.mp3",
            streaming=True,
            is_music=True,
        )
        self.background_music = cme.sound.play_sound(
            background_music_source,
            self.window.settings.volume,
        )
        self.background_music.pause()

        def start_background_music(dt: float):
            self.background_music.play()

        cme.concurrency.schedule_once(start_background_music, 1)

    def on_hide_view(self):
        super().on_hide_view()
        self.background_music.pause()
        self.background_music.delete()

    def on_draw(self) -> None:
        super().on_draw()
        self.text_batch.draw()
        self.pixel_sprites.draw(pixelated=True)

        # BUG This gets overdrawn by settings_menu, no matter the SpriteList
        # order
        self.settings_pointer_right.draw(pixelated=True)
        self.settings_pointer_left.draw(pixelated=True)

        if self.settings_menu.visible:
            self.settings_batch.draw()

        if self.rebind_overlay.visible:
            self.rebind_overlay.draw()
            self.rebind_text.draw()

        self.draw_fading()

    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.pointer_right.update_animation()
        self.pointer_left.update_animation()


class GameView(cme.view.FadingView):
    """
    View handling the main gameplay.
    """
    window: "Window"

    def setup(self) -> None:
        self.camera = Camera()
        self.resize()
        self.overdraw_cam = Camera()

        self.setup_player()

        self.current_map = "d1r1.tmj"
        self.setup_map()

    def resize(self):
        self.on_resize(self.window.width, self.window.height)

    def setup_player(self) -> None:
        self.player = Player()
        idle_textures = load_texture_series(
            dir=TEXTURES_PATH / "player",
            stem="player_idle_{i}.png",
            range_=range(1, 3),
            hit_box_algorithm=PymunkHitBoxAlgorithm(),
        )
        walking_textures = load_texture_series(
            dir=TEXTURES_PATH / "player",
            stem="player_idle_{i}.png",
            range_=range(1, 3),
            hit_box_algorithm=PymunkHitBoxAlgorithm(),
        )
        self.player.texture_add_idling(
            list(map(lambda x: (x,), idle_textures))
        )
        self.player.texture_add_walking(
            list(map(lambda x: (x,), walking_textures))
        )
        self.player.animation_speed = 1.0
        self.player.set_idling()

    def load_current_map(self):
        self.tilemap = cme.tilemap.TileMap(
            MAPS_PATH / self.current_map,
            use_spatial_hash=True
        )
        self.scene = Scene.from_tilemap(self.tilemap)

    def setup_map(self):
        self.load_current_map()
        self.player.position = MAP_SIZE / 2, MAP_SIZE / 2
        self.scene.add_sprite_list("enemies", use_spatial_hash=True)
        self.scene.add_sprite_list(
            "friendly_projectiles", use_spatial_hash=True)
        self.scene.add_sprite_list(
            "hostile_projectiles", use_spatial_hash=True)
        self.scene.add_sprite_list("player", use_spatial_hash=True)
        self.scene["player"].append(self.player)

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        self.map_scale = (
            width / MAP_SIZE if width < height else height / MAP_SIZE
        )
        self.camera.viewport = (
            (self.window.width - MAP_SIZE * self.map_scale) / 2,
            0,
            MAP_SIZE * self.map_scale,
            MAP_SIZE * self.map_scale,
        )
        self.camera.projection = (
            0, MAP_SIZE, 0, MAP_SIZE
        )
        self.camera.update()

    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.scene.on_update(delta_time)
        self.scene.update_animation(delta_time)
        bullets = self.player.shoot()
        if bullets:
            self.scene["friendly_projectiles"].extend(bullets)

        # Projectile collisions and out-of-bounds
        for projectile in (
            *self.scene["friendly_projectiles"],
            *self.scene["hostile_projectiles"],
        ):
            if (
                projectile.top < 0
                or projectile.bottom > MAP_SIZE
                or projectile.left < 0
                or projectile.right > MAP_SIZE
                or check_for_collision_with_list(
                    projectile, self.scene["walls"]
                )
            ):
                projectile.remove_from_sprite_lists()

    def on_draw(self) -> None:
        # Overdraw with black as the Camera only draws to its viewport.
        # Prevents issues with overlays from other apps.
        self.overdraw_cam.use()
        draw_xywh_rectangle_filled(
            0,
            0,
            self.window.width,
            self.window.height,
            csscolor.BLACK,
        )

        self.camera.use()
        super().on_draw()

        self.scene.draw(pixelated=True)

        self.draw_fading()

    def on_key_press(self, symbol: int, modifiers: int):
        super().on_key_press(symbol, modifiers)

        if symbol == self.window.settings.controls.move_up:
            self.player.up_pressed = True
        elif symbol == self.window.settings.controls.move_down:
            self.player.down_pressed = True
        elif symbol == self.window.settings.controls.move_left:
            self.player.left_pressed = True
        elif symbol == self.window.settings.controls.move_right:
            self.player.right_pressed = True
        elif symbol == self.window.settings.controls.use_item:
            self.player.use_item()
        elif symbol == self.window.settings.controls.shoot_up:
            self.player.shoot_up_pressed = True
        elif symbol == self.window.settings.controls.shoot_down:
            self.player.shoot_down_pressed = True
        elif symbol == self.window.settings.controls.shoot_left:
            self.player.shoot_left_pressed = True
        elif symbol == self.window.settings.controls.shoot_right:
            self.player.shoot_right_pressed = True

    def on_key_release(self, symbol: int, modifiers: int):
        super().on_key_release(symbol, modifiers)

        if symbol == self.window.settings.controls.move_up:
            self.player.up_pressed = False
        elif symbol == self.window.settings.controls.move_down:
            self.player.down_pressed = False
        elif symbol == self.window.settings.controls.move_right:
            self.player.right_pressed = False
        elif symbol == self.window.settings.controls.move_left:
            self.player.left_pressed = False
        elif symbol == self.window.settings.controls.shoot_up:
            self.player.shoot_up_pressed = False
        elif symbol == self.window.settings.controls.shoot_down:
            self.player.shoot_down_pressed = False
        elif symbol == self.window.settings.controls.shoot_left:
            self.player.shoot_left_pressed = False
        elif symbol == self.window.settings.controls.shoot_right:
            self.player.shoot_right_pressed = False

    def on_show_view(self) -> None:
        super().on_show_view()
        self.window.background_color = csscolor.BLACK
        self.start_fade_in()
