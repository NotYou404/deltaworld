from dataclasses import dataclass
from typing import Any, Mapping, Optional

import cme.resource_

from .model import Item, Upgrade

RGB = tuple[int, int, int]


class UnfinishedRun:
    def __init__(
        self,
        map: str,
        armor: Upgrade,
        gun: Upgrade,
        ammo: Upgrade,
        stored_item: Optional[Item],
        res_coins: int,
        hard: bool,
    ) -> None:
        """
        Save everything required to resume a game at a specific state.

        :param map: The map string the player is currently on. Example:
        `"d2r3"` for dimension 2 room 3.
        :type map: str
        :param armor: The Upgrade object describing the player's armor
        :type armor: Upgrade
        :param gun: The Upgrade object describing the player's gun
        :type gun: Upgrade
        :param ammo: The Upgrade object describing the player's ammo
        :type ammo: Upgrade
        :param stored_item: The Item object the player is currently storing
        :type stored_item: Optional[Item]
        :param res_coins: The amount of resurrection coins the player owns
        :type res_coins: int
        :param hard: Wether the run is in hard mode
        :type hard: bool
        """
        self.map = map
        self.armor = armor
        self.gun = gun
        self.ammo = ammo
        self.stored_item = stored_item
        self.res_coins = res_coins
        self.hard = hard


@dataclass
class GameSave(cme.resource_.PickleGameSave):
    """
    Class to handle all game saves. Handles (de-)serialization and saving.
    """
    def __init__(
        self,
        finished_normal: bool,
        finished_hard: bool,
        achievement_lawyer: bool,
        achievement_not_bug_feature: bool,
        achievement_poor_spectre: bool,
        achievement_unique_playstyle: bool,
        unfinished_run: Optional[UnfinishedRun],
    ):
        """
        :param finished_normal: Wether normal mode has been completed
        :type finished_normal: bool
        :param finished_hard: Wether hard mode has been completed
        :type finished_hard: bool
        :param achievement_lawyer: Wether the achievement has been achieved
        :type achievement_lawyer: bool
        :param achievement_not_bug_feature: Wether the achievement has been
        achieved
        :type achievement_not_bug_feature: bool
        :param achievement_poor_spectre: Wether the achievement has been
        achieved
        :type achievement_poor_spectre: bool
        :param achievement_unique_playstyle: Wether the achievement has been
        achieved
        :type achievement_unique_playstyle: bool
        :param unfinished_run: A run that can be continued, or None
        :type unfinished_run: Optional[UnfinishedRun]
        """
        self.finished_normal = finished_normal
        self.finished_hard = finished_hard
        self.achievement_lawyer = achievement_lawyer
        self.achievement_not_bug_feature = achievement_not_bug_feature
        self.achievement_poor_spectre = achievement_poor_spectre
        self.achievement_unique_playstyle = achievement_unique_playstyle
        self.unfinished_run = unfinished_run

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
            "achievement_lawyer": False,
            "achievement_not_bug_feature": False,
            "achievement_poor_spectre": False,
            "achievement_unique_playstyle": False,
            "unfinished_run": None,
        }

    def update(self, **kwargs: Mapping[str, Any]) -> None:
        """
        Update multiple entries at once. Pass entries as keyword arguments,
        e.g. using **dict.
        """
        for key_, value in kwargs.items():
            setattr(self, key_, value)
