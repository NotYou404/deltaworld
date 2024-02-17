from typing import TYPE_CHECKING, Any, Mapping

import cme.resource_
from cme import key, logger
from cme.utils import missing_keys

if TYPE_CHECKING:
    from window import Window


@cme.resource_.register_custom_settings_class
class Settings(cme.resource_.Settings):
    """
    Class to handle all saved settings. Handles (de-)serialization and saving.
    """
    def __init__(
        self,
        langcode: str,
        volume: int,
        controls: "Controls",
    ):
        """
        :param langcode: The language code the game should use as translation
        of game strings. Usually `"en_US"`.
        :type langcode: str
        :param volume: The game volume for both music and effects. 1-100.
        :type volume: int
        :param controls: A `Controls` instance to allow permanent customizing
        of controls.
        :type controls: Controls
        """
        self._langcode = langcode
        self._volume = volume
        self._controls = controls

    @property
    def langcode(self) -> str:
        return self._langcode

    @langcode.setter
    def langcode(self, value: str) -> None:
        self._langcode = value

    @property
    def volume(self) -> int:
        return self._volume

    @volume.setter
    def volume(self, value: int) -> None:
        if value < 0:
            value = 0
        elif value > 100:
            value = 100
        self._volume = value

    @property
    def controls(self) -> "Controls":
        return self._controls

    @controls.setter
    def controls(self, value: "Controls") -> None:
        self._controls = value

    def _serialize(self) -> dict[str, Any]:
        """
        Serialize the Settings object into a dictionary to allow further
        serialization into json.

        :return: The serialized dict.
        :rtype: dict[str, Any]
        """
        dict_ = {}
        attrs = self.defaults().keys()
        for attr in attrs:
            if attr == "controls":
                dict_[attr] = self.controls.serialize()
            else:
                dict_[attr] = getattr(self, attr)
        return dict_

    @classmethod
    def _deserialize(cls, dictionary: dict[str, Any]) -> "Settings":
        """
        Deserialize a previously serialized dictionary back into a Settings
        object.

        :param dictionary: The serialized dictionary.
        :type dictionary: dict[str, Any]
        :return: The resulting Settings object.
        :rtype: Settings
        """
        try:
            dictionary["controls"] = Controls(**dictionary["controls"])
        except TypeError:  # Attribute got removed or renamed
            controls = Controls.with_defaults()
            for k, v in dictionary["controls"].items():
                if hasattr(controls, k):
                    setattr(controls, k, v)
            dictionary["controls"] = controls
        defaults = cls.defaults()

        # These might have been added since last game start
        missing_keys_in_saved = missing_keys(defaults, dictionary)
        for key_ in missing_keys_in_saved:
            logger.info(
                f"Adding missing settings key {key_} with default "
                f"{defaults[key_]}."
            )
            dictionary[key_] = defaults[key_]

        # These might have been removed since last game start
        additional_keys_in_saved = missing_keys(dictionary, defaults)
        for key_ in additional_keys_in_saved:
            logger.info(f"Removing additional settings key {key_}.")
            dictionary.pop(key_)

        return cls(**dictionary)

    @staticmethod
    def defaults() -> dict[str, Any]:
        """
        Generates usable default settings as deserializable dictionary.

        :return: The default settings as dictionary.
        :rtype: dict[str, Any]
        """
        return {
            "langcode": "en_US",
            "volume": 100,
            "controls": Controls.with_defaults().serialize(),
        }

    def update(self, **kwargs: Mapping[str, Any]) -> None:
        """
        Update multiple settings at once. Pass settings as keyword arguments,
        e.g. using **dict.
        """
        for key_, value in kwargs.items():
            setattr(self, key_, value)

    def apply(self, window: "Window") -> None:
        """
        Apply all settings to the active game window.

        :param window: The window to apply the settings to.
        :type window: Window
        """
        window.set_language(self.langcode)
        window.set_volume()


class Controls:
    """
    A class to represent a state of internal controls to physical keys.
    """
    def __init__(
        self,
        move_up: int,
        move_down: int,
        move_left: int,
        move_right: int,
        shoot_up: int,
        shoot_down: int,
        shoot_left: int,
        shoot_right: int,
        use_item: int,
    ):
        """
        :param move_up: Move upwards.
        :type move_up: int
        :param move_down: Move downwards.
        :type move_down: int
        :param move_left: Move left.
        :type move_left: int
        :param move_right: Move right.
        :type move_right: int
        :param shoot_up: Shoot up.
        :type shoot_up: int
        :param shoot_down: Shoot down.
        :type shoot_down: int
        :param shoot_left: Shoot left.
        :type shoot_left: int
        :param shoot_right: Shoot right.
        :type shoot_right: int
        :param item: Use the current item.
        :type item: int
        """
        self.move_up = move_up
        self.move_down = move_down
        self.move_left = move_left
        self.move_right = move_right
        self.shoot_up = shoot_up
        self.shoot_down = shoot_down
        self.shoot_left = shoot_left
        self.shoot_right = shoot_right
        self.use_item = use_item

    def serialize(self) -> dict[str, Any]:
        """
        Serialize the Controls object into a dictionary to allow further
        serialization into json.

        :return: The serialized dict.
        :rtype: dict[str, Any]
        """
        dict_ = {}
        attrs = self.defaults().keys()
        for attr in attrs:
            dict_[attr] = getattr(self, attr)
        return dict_

    @staticmethod
    def defaults() -> dict[str, Any]:
        """
        Generates usable default settings as deserializable dictionary.

        :return: The default settings as dictionary.
        :rtype: dict[str, Any]
        """
        return {
            "move_up": key.W,
            "move_down": key.S,
            "move_left": key.A,
            "move_right": key.D,
            "shoot_up": key.UP,
            "shoot_down": key.DOWN,
            "shoot_left": key.LEFT,
            "shoot_right": key.RIGHT,
            "use_item": key.SPACE,
        }

    @classmethod
    def with_defaults(cls) -> "Controls":
        return cls(**cls.defaults())

    def to_dict(self):
        keys = self.defaults().keys()
        values = [getattr(self, key) for key in keys]
        return {k: v for k, v in zip(keys, values)}
