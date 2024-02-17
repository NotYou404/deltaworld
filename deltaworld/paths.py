from pathlib import Path

import cme.resource_

cme.resource_.set_assets_path(Path(__file__).parent / "assets")
ASSETS_PATH = cme.resource_.get_assets_path()

FONTS_PATH = cme.resource_.AssetsPath(ASSETS_PATH / "fonts")

IMAGES_PATH = cme.resource_.AssetsPath(ASSETS_PATH / "images")

SOUNDS_PATH = cme.resource_.AssetsPath(ASSETS_PATH / "sounds")

MUSIC_PATH = cme.resource_.AssetsPath(ASSETS_PATH / "music")

TEXTURES_PATH = cme.resource_.AssetsPath(ASSETS_PATH / "textures")

MAPS_PATH = cme.resource_.AssetsPath(ASSETS_PATH / "maps")
