import math
import time
from typing import Any, Iterable, Optional

import cme.utils
from cme.sprite import AnimatedWalkingSprite, Sprite, TopDownUpdater

from .paths import TEXTURES_PATH
from .constants import MAP_SIZE


def speed(speed: float, factor: float = 140) -> float:
    """
    Convert a model speed into speed in pixels. Default factor is 140, factor
    should be consistent throughout the game.

    :param speed: The model speed (e.g. 1 as base for the player).
    :type speed: float
    :return: The speed in pixels per seconds.
    :rtype: float
    """
    return speed * factor


def find_with_class(iter: Iterable, cls: type | tuple[type]) -> Optional[Any]:
    """
    Searches the given iterable for an item with the given class. Returns the
    first find.

    :param iter: Iterable to scan.
    :type iter: Iterable
    :param cls: A type or list of types the target should match with.
    :type cls: type | tuple[type]
    :return: The first item with the desired type, if any.
    :rtype: Optional[Any]
    """
    for obj in iter:
        if isinstance(obj, cls):
            return obj


class Upgrade:
    def __init__(self, level: int = 0) -> None:
        self.level = level

    def upgrade(self) -> int:
        """Upgrade and return new level."""
        self.level += 1
        return self.level


class Item:
    RARE: bool
    DURATION: int | float

    def __init__(self):
        self.time_used: Optional[float] = None

    def use(self):
        self.time_used = time.time()


class SemiAutomatic(Item):
    RARE = False
    DURATION = 12
    FIRE_RATE = 10


class Pressurer(Item):
    RARE = True
    DURATION = 12
    BULLET_SPEED_MOD = 1.5
    DAMAGE_MOD = 2.0


class Scope(Item):
    RARE = False
    DURATION = 18
    EXTRA_PENETRATION = 1
    FIRE_RATE_MOD = 0.8


class BlueCow(Item):
    RARE = False
    DURATION = 15
    SPEED_MOD = 1.35


class Spray(Item):
    RARE = False
    DURATION = 13


class ThreeSixty(Item):
    RARE = False
    DURATION = 12


class HolyGuard(Item):
    RARE = True
    DURATION = 8
    IMMUNITY_DURATION = 3


class SmokeBomb(Item):
    RARE = True
    DURATION = 7


class LaserBeam(Item):
    RARE = True
    DURATION = 15
    SECONDS_PER_CYCLE = 1.5
    RANGE = 3
    DAMAGE = 8


class Bullet(Sprite):
    def __init__(
        self,
        damage: int = 1,
        penetration: int = 0,
        path_or_texture: cme.types.PathOrTexture = None,
        scale: float = 1.0,
        center_x: float = 0.0,
        center_y: float = 0.0,
        angle: float = 0.0,
        **kwargs,
    ):
        super().__init__(
            path_or_texture=path_or_texture,
            scale=scale,
            center_x=center_x,
            center_y=center_y,
            angle=angle,
            **kwargs
        )
        self.damage = damage
        self.penetration = penetration  # Kept for statistic
        self.remaining_penetration = penetration


class Player(AnimatedWalkingSprite):
    BASE_DAMAGE = 1
    BASE_SPEED = 1
    BASE_FIRE_RATE = 3
    BASE_BULLET_SPEED = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.armor = Upgrade()
        self.gun = Upgrade()
        self.ammo = Upgrade()
        self.stored_item: Optional[Item] = None
        self.res_coins = 0
        self.active_items: list[Item] = []
        self.last_shot: float = time.time()
        self.facing_angle = 0
        self.is_on_soulsand = False

        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.shoot_left_pressed = False
        self.shoot_right_pressed = False
        self.shoot_up_pressed = False
        self.shoot_down_pressed = False

        self.walls: Iterable[Sprite] = []

    def calc_facing_angle(self) -> int:
        if self.change_x == 0 and self.change_y == 0:
            return self.facing_angle  # Standing still

        # In Cartesian standard, 0° is the positive X axis (right), going
        # counterclockwise. Positive Y (top) is therefore 90°.
        elif self.change_x == 0 and self.change_y > 0:
            return 90  # Move up
        elif self.change_x == 0 and self.change_y < 0:
            return 270  # Move down
        elif self.change_x > 0 and self.change_y == 0:
            return 0  # Move right
        elif self.change_x < 0 and self.change_y == 0:
            return 180  # Move left

        elif self.change_x > 0 and self.change_y > 0:
            return 45  # Move top right
        elif self.change_x > 0 and self.change_y < 0:
            return 315  # Move bottom right
        elif self.change_x < 0 and self.change_y < 0:
            return 225  # Move bottom left
        elif self.change_x < 0 and self.change_y > 0:
            return 135  # Move top left

    def on_update(
        self,
        delta_time: float,
    ) -> None:

        # Movement logic
        dir_horizontal = 0
        dir_vertical = 0
        if self.right_pressed:
            dir_horizontal += 1
        if self.left_pressed:
            dir_horizontal -= 1
        if self.up_pressed:
            dir_vertical += 1
        if self.down_pressed:
            dir_vertical -= 1
        if dir_horizontal and not dir_vertical:
            self.change_x = dir_horizontal * speed(self.final_movement_speed)
            self.change_y = 0
        elif dir_vertical and not dir_horizontal:
            self.change_x = 0
            self.change_y = dir_vertical * speed(self.final_movement_speed)
        elif not dir_horizontal and not dir_vertical:
            self.change_x = 0
            self.change_y = 0
        else:
            if dir_horizontal > 0 and dir_vertical > 0:
                self.change_x, self.change_y = cme.utils.calc_change_x_y(
                    speed(self.final_movement_speed), 45
                )
            elif dir_horizontal < 0 and dir_vertical > 0:
                self.change_x, self.change_y = cme.utils.calc_change_x_y(
                    speed(self.final_movement_speed), 135
                )
            elif dir_horizontal < 0 and dir_vertical < 0:
                self.change_x, self.change_y = cme.utils.calc_change_x_y(
                    speed(self.final_movement_speed), 225
                )
            else:
                self.change_x, self.change_y = cme.utils.calc_change_x_y(
                    speed(self.final_movement_speed), 315
                )

        super().on_update(
            delta_time, TopDownUpdater(self.walls, (0, 0, MAP_SIZE, MAP_SIZE))
        )

        # Set facing by walk direction
        self.facing_angle = self.calc_facing_angle()

        # Remove timed out items
        cur_time = time.time()
        for item in self.active_items.copy():
            if item.time_used > cur_time - item.DURATION:
                self.active_items.remove(item)

    def use_item(self):
        if not self.stored_item:
            return

        # Only one item of a type can be active at once
        for item in self.active_items.copy():
            if isinstance(item, self.stored_item.__class__):
                self.active_items.remove(item)

        self.active_items.append(self.stored_item)
        self.stored_item.use()
        self.stored_item = None

    def shoot(self) -> Optional[list[Sprite]]:
        """
        Create and move bullet sprites. Returns a list of bullets to be added
        to the scene, or None, if the player can't shoot at the moment.

        :return: A list of bullet sprites to be added to the scene object. None
        if the shooting cooldown isn't over yet.
        :rtype: Optional[list[Sprite]]
        """
        if self.last_shot > time.time() - 1 / self.final_fire_rate:
            return  # Can't shoot that fast

        # Calculate shooting angle
        dir_horizontal = 0
        dir_vertical = 0
        if self.shoot_right_pressed:
            dir_horizontal += 1
        if self.shoot_left_pressed:
            dir_horizontal -= 1
        if self.shoot_up_pressed:
            dir_vertical += 1
        if self.shoot_down_pressed:
            dir_vertical -= 1
        if not dir_horizontal and not dir_vertical:
            # Either not shooting at all, or holding two opposing buttons
            return
        if dir_horizontal and not dir_vertical:
            shoot_angle = 0 if dir_horizontal > 0 else 180
        elif dir_vertical and not dir_horizontal:
            shoot_angle = 90 if dir_vertical > 0 else 270
        # We don't need a case for no angle here as that means that we
        # should'nt shoot
        else:
            if dir_horizontal > 0 and dir_vertical > 0:
                shoot_angle = 45
            elif dir_horizontal < 0 and dir_vertical > 0:
                shoot_angle = 135
            elif dir_horizontal < 0 and dir_vertical < 0:
                shoot_angle = 225
            else:
                shoot_angle = 315

        bullets = []
        bullet_speed = self.final_bullet_speed
        bullet_damage = self.final_damage
        bullet_penetration = self.final_penetration

        if find_with_class(self.active_items, Spray):
            for angle in (
                shoot_angle - 45,
                shoot_angle - 22.5,
                # We don't want the middle as it's added anyways
                shoot_angle + 22.5,
                shoot_angle + 45,
            ):
                bullet = Bullet(
                    damage=bullet_damage,
                    penetration=bullet_penetration,
                    path_or_texture=TEXTURES_PATH / "bullet.png",
                    center_x=self.center_x,
                    center_y=self.center_y,
                    angle=angle,
                )
                bullet.change_x, bullet.change_y = cme.utils.calc_change_x_y(
                    speed(bullet_speed), angle
                )
                bullets.append(bullet)

        if find_with_class(self.active_items, ThreeSixty):
            for angle in (
                # We don't want the middle as it's added anyways
                shoot_angle + 45,
                shoot_angle + 90,
                shoot_angle + 135,
                shoot_angle + 180,
                shoot_angle + 225,
                shoot_angle + 270,
                shoot_angle + 315,
            ):
                bullet = Bullet(
                    damage=bullet_damage,
                    penetration=bullet_penetration,
                    path_or_texture=TEXTURES_PATH / "bullet.png",
                    center_x=self.center_x,
                    center_y=self.center_y,
                    angle=angle,
                )
                bullet.change_x, bullet.change_y = cme.utils.calc_change_x_y(
                    speed(bullet_speed), angle
                )
                bullets.append(bullet)

        default_bullet = Bullet(
            damage=bullet_damage,
            penetration=bullet_penetration,
            path_or_texture=TEXTURES_PATH / "bullet.png",
            center_x=self.center_x,
            center_y=self.center_y,
            angle=shoot_angle,
        )
        default_bullet.change_x, default_bullet.change_y = (
            cme.utils.calc_change_x_y(
                speed(bullet_speed), shoot_angle
            )
        )
        bullets.append(default_bullet)

        self.last_shot = time.time()

        return bullets

    @property
    def final_damage(self):
        """
        Get the damage done with a single shot, taking ammo and items into
        account.
        """
        damage = self.BASE_DAMAGE + self.BASE_DAMAGE * 0.5 * self.ammo.level
        if item := find_with_class(self.active_items, Pressurer):
            damage *= item.DAMAGE_MOD
        return math.floor(damage)

    @property
    def final_fire_rate(self):
        """Get the gun's fire rate, taking gun level and items into account."""
        rate = self.BASE_FIRE_RATE + self.BASE_FIRE_RATE * 0.2 * self.gun.level
        if item := find_with_class(self.active_items, SemiAutomatic):
            rate = item.FIRE_RATE
        if item := find_with_class(self.active_items, Scope):
            rate *= item.FIRE_RATE_MOD
        return rate

    @property
    def final_penetration(self):
        """
        Get the gun's penetration, taking gun level and items into account.
        """
        penetration = 1 * 0.5 * self.gun.level
        if item := find_with_class(self.active_items, Scope):
            penetration += item.EXTRA_PENETRATION
        return math.floor(penetration)

    @property
    def final_movement_speed(self):
        """
        Get the player's movement speed, taking armor level and items into
        account.
        """
        speed = self.BASE_SPEED + self.BASE_SPEED * 0.2 * self.armor.level
        if item := find_with_class(self.active_items, BlueCow):
            speed *= item.SPEED_MOD
        if self.is_on_soulsand:
            speed -= 0.4
        return speed

    @property
    def final_bullet_speed(self):
        """Get bullet speed, taking items into account."""
        speed = self.BASE_BULLET_SPEED
        if item := find_with_class(self.active_items, Pressurer):
            speed *= item.BULLET_SPEED_MOD
        return speed
