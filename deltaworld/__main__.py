import sys
from pathlib import Path

import cme
import cme.font
import cme.localization
from cme import logger


def launch():
    cme.localization.LangDict.set_languages_path(
        Path(__file__).parent / "langs"
    )

    from .paths import FONTS_PATH
    cme.font.load_font(FONTS_PATH / "november" / "novem___.ttf")

    from .window import Window
    from .views import MenuView

    win = Window(
        title="Deltaworld",
        fullscreen=True,
        vsync=True,
    )

    menu_view = MenuView()
    menu_view.setup()
    win.show_view(menu_view)

    try:
        cme.run()
    except Exception as e:
        logger.critical(
            f"Uncatched {type(e).__name__} on mainloop. See exc_info output.",
            exc_info=True,
        )
        raise
    sys.exit(0)


if __name__ == "__main__":
    cme.init_cme("Deltaworld")
    from cme import resource_

    logger.configure_logger(
        logs_path=resource_.LOGS_PATH,
        level=None,  # Will be set according to __debug__
    )

    launch()
