from typing import TYPE_CHECKING

import cme.text
import cme.view
from cme import csscolor, key
from cme.sprite import AnimatedSprite, Sprite, SpriteList
from cme.texture import Texture, load_texture

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
        self.sprites = SpriteList()
        self.pixel_sprites = SpriteList()

        self.header = cme.text.create_text_sprite(
            text=self.window.lang["deltaworld"],
            color=csscolor.WHITE,
            font_size=72,
            font_name=Font.november,
        )
        self.start_game = cme.text.create_text_sprite(
            text=self.window.lang["start_game"],
            color=csscolor.WHITE,
            font_size=24,
            font_name=Font.november,
        )
        self.settings = cme.text.create_text_sprite(
            text=self.window.lang["options"],
            color=csscolor.WHITE,
            font_size=24,
            font_name=Font.november,
        )
        self.quit = cme.text.create_text_sprite(
            text=self.window.lang["quit"],
            color=csscolor.WHITE,
            font_size=24,
            font_name=Font.november,
        )
        self.sprites.extend([
            self.header, self.start_game, self.settings, self.quit
        ])
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

    def on_resize(self, width: int, height: int) -> None:
        self.header.center_x = width / 2
        self.header.center_y = height / 1.4
        self.start_game.center_x = width / 2
        self.start_game.center_y = height / 2.4
        self.settings.center_x = width / 2
        self.settings.center_y = self.start_game.center_y - 50
        self.quit.center_x = width / 2
        self.quit.center_y = self.settings.center_y - 50

        self.pointer_right.center_x = self.selected_item.left - 40
        self.pointer_right.center_y = self.selected_item.center_y
        self.pointer_left.center_x = self.selected_item.right + 40
        self.pointer_left.center_y = self.selected_item.center_y

        self.settings_menu.center_x = self.window.width / 2
        self.settings_menu.center_y = self.window.height / 2
        self.settings_menu_header.center_x = self.window.width / 2
        self.settings_menu_header.center_y = self.settings_menu.top - 80
        self.settings_tooltip.center_x = self.window.width / 2
        self.settings_tooltip.center_y = self.settings_menu_header.center_y - 40  # noqa
        self.settings_lang_label.center_x = self.window.width / 2
        self.settings_lang_label.center_y = self.settings_tooltip.center_y - 80
        self.settings_lang_switch.center_x = self.window.width / 2
        self.settings_lang_switch.center_y = self.settings_lang_label.center_y - 40  # noqa
        self.settings_volume_label.center_x = self.window.width / 2
        self.settings_volume_label.center_y = self.settings_lang_switch.center_y - 60  # noqa
        self.settings_volume_switch.center_x = self.window.width / 2
        self.settings_volume_switch.center_y = self.settings_volume_label.center_y - 40  # noqa
        self.settings_controls_label.center_x = self.window.width / 2
        self.settings_controls_label.center_y = self.settings_volume_label.center_y - 80  # noqa

        item_above = self.settings_controls_label
        for control in self.settings_controls:
            control.center_x = self.window.width / 2
            control.center_y = item_above.center_y - 40
            item_above = control

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

    def create_settings_menu(self):
        self.settings_entries = SpriteList()

        self.settings_menu = Sprite(
            path_or_texture=load_texture(
                TEXTURES_PATH / "menus" / "settings.png"
            ),
            scale=25,
        )
        self.settings_menu_header = cme.text.create_text_sprite(
            text=self.window.lang["options"],
            color=csscolor.WHITE,
            font_size=32,
            font_name=Font.november,
        )
        self.settings_tooltip = cme.text.create_text_sprite(
            text=self.window.lang["use_arrows_to_switch_value"],
            color=csscolor.WHITE,
            font_size=20,
            font_name=Font.november,
        )
        self.settings_lang_label = cme.text.create_text_sprite(
            text=self.window.lang["language"],
            color=csscolor.WHITE,
            font_size=18,
            font_name=Font.november,
        )
        self.settings_lang_switch = cme.text.create_text_sprite(
            text=self.window.lang.name,
            color=csscolor.WHITE,
            font_size=20,
            font_name=Font.november,
        )
        self.settings_volume_label = cme.text.create_text_sprite(
            text=self.window.lang["volume"],
            color=csscolor.WHITE,
            font_size=18,
            font_name=Font.november,
        )
        self.settings_volume_switch = cme.text.create_text_sprite(
            text=str(self.window.settings.volume),
            color=csscolor.WHITE,
            font_size=20,
            font_name=Font.november,
        )
        self.settings_controls_label = cme.text.create_text_sprite(
            text=self.window.lang["controls"],
            color=csscolor.WHITE,
            font_size=26,
            font_name=Font.november,
        )

        controls = self.window.settings.controls
        self.settings_controls = []
        for setting in ("move_up", "move_down", "move_left", "move_right",
                        "shoot_up", "shoot_down", "shoot_left", "shoot_right",
                        "item"):
            self.settings_controls.append(
                cme.text.create_text_sprite(
                    text=self.window.lang[setting].format(
                        key=getattr(controls, setting)
                    ),
                    color=csscolor.WHITE,
                    font_size=18,
                    font_name=Font.november,
                )
            )

        self.settings_back = cme.text.create_text_sprite(
            text=self.window.lang["back"],
            color=csscolor.WHITE,
            font_size=20,
            font_name=Font.november,
        )

        self.pixel_sprites.append(self.settings_menu)
        self.settings_entries.extend([
            self.settings_menu_header, self.settings_tooltip,
            self.settings_lang_label, self.settings_lang_switch,
            self.settings_volume_label, self.settings_volume_switch,
            self.settings_controls_label,
        ])
        self.settings_entries.extend(self.settings_controls)

        self.on_resize(self.window.width, self.window.height)

    def show_settings_menu(self):
        self.settings_menu.visible = True
        self.settings_entries.visible = True

    def hide_settings_menu(self):
        self.settings_menu.visible = False
        self.settings_entries.visible = False

    def on_show_view(self) -> None:
        super().on_show_view()
        self.window.background_color = csscolor.BLACK
        self.start_fade_in()

    def on_draw(self) -> None:
        super().on_draw()
        self.sprites.draw()
        self.pixel_sprites.draw(pixelated=True)
        self.settings_entries.draw()
        self.draw_fading()

    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.pointer_right.update_animation()
        self.pointer_left.update_animation()
