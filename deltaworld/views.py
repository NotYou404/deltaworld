from typing import TYPE_CHECKING

import cme.localization
import cme.text
from cme.text import center_x
import cme.view
from cme import csscolor, key
from cme.sprite import AnimatedSprite, Sprite, SpriteList
from cme.texture import Texture, load_texture

from pyglet.graphics import Batch

from .enums import Font
from .paths import TEXTURES_PATH

if TYPE_CHECKING:
    from .window import Window


class MenuView(cme.view.FadingView):
    """
    View that appears right when starting the game. Shows a splash screen with
    the game name.
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

    def on_key_press(self, symbol: int, modifiers: int):
        super().on_key_press(symbol, modifiers)
        if symbol == key.UP:
            if self.selected_item == self.settings:
                self.selected_item = self.start_game
            elif self.selected_item == self.quit:
                self.selected_item = self.settings
            self.on_resize(self.window.width, self.window.height)
        elif symbol == key.DOWN:
            if self.selected_item == self.start_game:
                self.selected_item = self.settings
            elif self.selected_item == self.settings:
                self.selected_item = self.quit
            self.on_resize(self.window.width, self.window.height)
        elif symbol == key.ENTER:
            if self.selected_item == self.start_game:
                self.next_view = GameView
                self.start_fade_out()
            elif self.selected_item == self.settings:
                self.show_settings_menu()
            else:
                self.window.close()

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
                    self.window.set_language(next_code)
                    self.apply_language()
                    self.settings_lang_switch.text = self.window.lang.name
                    self.on_resize(self.window.width, self.window.height)

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
        for entry, setting in zip(self.settings_entries[9:], (
            "move_up", "move_down", "move_left", "move_right",
            "shoot_up", "shoot_down", "shoot_left", "shoot_right", "item"
        )):
            entry.text = self.window.lang[setting].format(
                key=getattr(self.window.settings.controls, setting)
            )
        self.settings_back.text = self.window.lang["back"]

    def create_settings_menu(self):
        self.settings_entries = []

        self.settings_menu = Sprite(
            path_or_texture=load_texture(
                TEXTURES_PATH / "menus" / "settings.png"
            ),
            scale=25,
        )
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
            font_size=20,
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
            font_size=20,
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
            text=str(self.window.settings.volume),
            start_x=0,
            start_y=0,
            color=csscolor.WHITE,
            font_size=20,
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
        for _ in ("move_up", "move_down", "move_left", "move_right",
                  "shoot_up", "shoot_down", "shoot_left", "shoot_right",
                  "item"):
            self.settings_controls.append(
                cme.text.Text(
                    text="",
                    start_x=0,
                    start_y=0,
                    color=csscolor.WHITE,
                    font_size=18,
                    font_name=Font.november,
                    batch=self.settings_batch,
                )
            )

        self.settings_back = cme.text.Text(
            text="",
            start_x=0,
            start_y=0,
            color=csscolor.WHITE,
            font_size=20,
            font_name=Font.november,
            batch=self.settings_batch,
        )

        self.pixel_sprites.append(self.settings_menu)
        self.settings_entries.extend([
            self.settings_menu_header, self.settings_tooltip,
            self.settings_lang_label, self.settings_lang_switch,
            self.settings_volume_label, self.settings_volume_switch,
            self.settings_controls_label, self.settings_back,
        ])
        self.settings_entries.extend(self.settings_controls)

        self.on_resize(self.window.width, self.window.height)

    def show_settings_menu(self):
        self.settings_menu.visible = True

    def hide_settings_menu(self):
        self.settings_menu.visible = False

    def on_show_view(self) -> None:
        super().on_show_view()
        self.window.background_color = csscolor.BLACK
        self.start_fade_in()

    def on_draw(self) -> None:
        super().on_draw()
        self.text_batch.draw()
        self.pixel_sprites.draw(pixelated=True)
        if self.settings_menu.visible:
            self.settings_batch.draw()
        self.draw_fading()

    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.pointer_right.update_animation()
        self.pointer_left.update_animation()
