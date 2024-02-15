from dataclasses import dataclass
from typing import Any, Mapping

import cme.resource_

RGB = tuple[int, int, int]


@dataclass
class GameSave(cme.resource_.PickleGameSave):
    """
    Class to handle all game saves. Handles (de-)serialization and saving.
    """
    def __init__(
        self,
        finished_normal: bool,
        finished_hard: bool,
    ):
        """
        :param finished_normal: Wether normal mode has been completed
        :type finished_normal: bool
        :param finished_hard: Wether hard mode has been completed
        :type finished_hard: bool
        """
        self.finished_normal = finished_normal
        self.finished_hard = finished_hard

    @staticmethod
    def defaults() -> dict[str, Any]:
        """
        Generates usable default game save as deserializable dictionary.

        :return: The default game save as dictionary.
        :rtype: dict[str, Any]
        """
        return {
            "finished_normal": False,
            "finished_hard": False,
        }

    def update(self, **kwargs: Mapping[str, Any]) -> None:
        """
        Update multiple entries at once. Pass entries as keyword arguments,
        e.g. using **dict.
        """
        for key_, value in kwargs.items():
            setattr(self, key_, value)
