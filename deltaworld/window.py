from json import JSONDecodeError
from pickle import UnpicklingError
from typing import Optional

import cme.concurrency
import cme.localization
import cme.resource_
import cme.sound
import cme.window
import pyglet
from cme import key, logger
from cme.resource_ import load_pickle_game_save, save_pickle_game_save

from .gamesave import GameSave
from .settings import Settings


class Window(cme.window.Window):
    """The games main window."""
    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: Optional[str] = 'Deltaworld',
        fullscreen: bool = False,
        resizable: bool = True,
        update_rate: float = 1 / 60,
        antialiasing: bool = True,
        gl_version: tuple[int, int] = (3, 3),
        screen: pyglet.canvas.Screen = None,
        style: Optional[str] = pyglet.window.Window.WINDOW_STYLE_DEFAULT,
        visible: bool = True,
        vsync: bool = False,
        gc_mode: str = "context_gc",
        center_window: bool = True,
        samples: int = 4,
        enable_polling: bool = True,
    ) -> None:
        super().__init__(
            width=width,
            height=height,
            title=title,
            fullscreen=fullscreen,
            resizable=resizable,
            update_rate=update_rate,
            antialiasing=antialiasing,
            gl_version=gl_version,
            screen=screen,
            style=style,
            visible=visible,
            vsync=vsync,
            gc_mode=gc_mode,
            center_window=center_window,
            samples=samples,
            enable_polling=enable_polling,
        )

        self.set_min_size(1330, 900)

        try:
            self.settings: Settings = cme.resource_.load_settings()
        except FileNotFoundError:
            self.settings = Settings.with_defaults()
        except JSONDecodeError:
            logger.critical("Settings file corrupt or empty.", exc_info=True)
            raise
        self.settings.apply(self)

        try:
            self.gamesave: GameSave = load_pickle_game_save(GameSave)
        except FileNotFoundError:
            self.gamesave = GameSave.with_defaults()
        except (UnpicklingError, EOFError):
            logger.critical("Game save file corrupt or empty.", exc_info=True)
            raise

    def set_language(self, langcode: str) -> None:
        """
        Set the translation used to display game strings.

        :param langcode: The language code in a `lang_COUNTRY` style. Typically
        `"en_US"`.
        :type langcode: str
        """
        self.lang = cme.localization.LangDict.from_langcode(langcode)

    def set_volume(self) -> None:
        for player in cme.sound.get_all_player_instances():
            player.volume = self.settings.volume

    def on_key_press(self, symbol: int, modifiers: int):
        super().on_key_press(symbol, modifiers)
        if symbol == key.F11:
            self.set_fullscreen(not self.fullscreen)
            self.center_window()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

    def close(self) -> None:
        self.on_close()

    def on_close(self) -> None:
        cme.resource_.save_settings(self.settings)
        save_pickle_game_save(self.gamesave)
        super().close()
