import math
import multiprocessing
import multiprocessing.pool
import multiprocessing.queues
import random
import time
import tomllib
from collections import deque
from multiprocessing import Process
from pathlib import Path
from typing import Any, Iterable, Optional

import cme.utils
from cme import types
from cme.pathfinding import AStarBarrierList, astar_calculate_path
from cme.sprite import (AnimatedSprite, AnimatedWalkingSprite, SimpleUpdater,
                        Sprite, SpriteList, TopDownUpdater, WallBounceUpdater)
from cme.texture import load_texture

from .constants import MAP_SIZE, TILE_SIZE
from .paths import TEXTURES_PATH

PATHFINDING_QUEUE: Optional[multiprocessing.Queue] = None  # type: ignore[type-arg]  # noqa
PATHFINDING_POOL: Optional[multiprocessing.pool.Pool] = None


def enqueue_pathfinder(
    sprite: Sprite,
    target_point: types.Point,
    walls: SpriteList,
) -> multiprocessing.pool.AsyncResult[Any]:
    global PATHFINDING_POOL
    if not PATHFINDING_POOL:
        PATHFINDING_POOL = multiprocessing.Pool(3)
    sprite = (
        sprite.texture.file_path,
        sprite.scale,
        sprite.center_x,
        sprite.center_y,
        sprite.angle,
    )
    walls = [
        (
            sprite.texture.file_path,
            sprite.scale,
            sprite.center_x,
            sprite.center_y,
            sprite.angle,
        )
        for sprite in walls
    ]
    return PATHFINDING_POOL.apply_async(
        _calc_path_pkl, (sprite, target_point, walls)
    )


def _calc_path_pkl(
    sprite: tuple[types.PathOrTexture, float, float, float, float],
    target_point: types.Point,
    walls: list[tuple[types.PathOrTexture, float, float, float, float]],
) -> Optional[list[types.Point]]:
    """
    We serialize Sprite and SpriteList with the minimal things required to
    enable pickling. For some reason I couldn't figure out, pickling (even
    with dill) a Sprite and SpriteList would raise an error, unable to pickle
    weakref (ctypes pointer object in the case of dill).

    sprite: tuple of texture path, scale, center_x, center_y, angle
    target_point: regular types.Point
    walls: list of tuples whose contents are same as with `sprite`

    Returns: Path returned by `calc_path()`
    """
    sprite = Sprite(
        path_or_texture=sprite[0],
        scale=sprite[1],
        center_x=sprite[2],
        center_y=sprite[3],
        angle=sprite[4],
    )
    walls_ = SpriteList()
    for wall in walls:
        walls_.append(Sprite(
            wall[0], wall[1], wall[2], wall[3], wall[4]
        ))
    return calc_path(sprite, target_point, walls_)


def calc_path(
    sprite: Sprite,
    target_point: types.Point,
    walls: SpriteList,
) -> Optional[list[types.Point]]:
    # As the algorithm doesn't allow moving on tiles instead of between tiles,
    # We need to manually displace walls and modify the path after calculating.
    for wall in walls:
        wall.center_x -= TILE_SIZE / 2
        wall.center_y -= TILE_SIZE / 2

    barrier_list = AStarBarrierList(
        moving_sprite=sprite,
        blocking_sprites=walls,
        grid_size=TILE_SIZE,
        left=TILE_SIZE / 2,
        right=MAP_SIZE + TILE_SIZE / 2,
        bottom=TILE_SIZE / 2,
        top=MAP_SIZE + TILE_SIZE / 2,
    )
    path: Optional[list[types.Point]] = astar_calculate_path(
        start_point=(sprite.center_x, sprite.center_y),
        end_point=get_tile_center_of_point(target_point),
        astar_barrier_list=barrier_list,
    )

    for wall in walls:
        wall.center_x += TILE_SIZE / 2
        wall.center_y += TILE_SIZE / 2

    if not path:
        return path

    # Shift path by 1/2 tiles as hostiles should walk on tiles, not between
    return [(p[0] + TILE_SIZE / 2, p[1] + TILE_SIZE / 2) for p in path]


def get_tile_center_of_point(
    point: types.Point
) -> Optional[tuple[float, float]]:
    for tile_x in range(0, MAP_SIZE, TILE_SIZE):
        for tile_y in range(0, MAP_SIZE, TILE_SIZE):
            rect = types.LBWH(tile_x, tile_y, TILE_SIZE, TILE_SIZE)
            if cme.utils.point_in_rect(*point, rect=rect):
                return (tile_x + TILE_SIZE / 2, tile_y + TILE_SIZE / 2)
    return None


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


def find_with_class(
    iter: Iterable[Any],
    cls: type | tuple[type],
) -> Optional[Any]:
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
    return None


class Level:
    def __init__(self, path: Path | str):
        """
        :param path: Path to the toml specs file.
        :type path: Path | str
        """
        with open(path, mode="rb") as fp:
            specs = tomllib.load(fp)

        self.mobs_probabilities: dict[str, float] = specs["mobs_probabilities"]
        self.mobs_extras: dict[str, dict[str, int]] = specs["mobs_extras"]
        self.waves: list[tuple[str | int, int]] = specs["waves"]
        self.special_waves: dict[str, dict[str, int]] = specs["special_waves"]

        self.current_wave = 0
        self.last_wave = len(self.waves) - 1

    def _calculate_wave_distribution(self, wave: int) -> list[str]:
        """
        Calculate the mob distribution for a given wave by defined
        probabilities (randomized).

        :param wave: Wave index
        :type wave: int
        :raises RuntimeError: Wave is a special wave
        :return: List of mob names
        :rtype: list[str]
        """
        mobs = self.waves[wave][0]
        if isinstance(mobs, str):
            raise RuntimeError("Cannot calculate special wave")
        return random.choices(
            population=list(self.mobs_probabilities.keys()),
            weights=self.mobs_probabilities.values(),  # type: ignore[arg-type]
            k=mobs,
        )

    def _get_special_wave_distribution(self, wave: int) -> list[str]:
        """
        Get a list of mob names for special waves.

        :param wave: Wave index
        :type wave: int
        :raises RuntimeError: The specified wave is not a special wave.
        :return: List of mob names
        :rtype: list[str]
        """
        name = self.waves[wave][0]
        if not isinstance(name, str):
            raise RuntimeError(f"Wave {wave} is not a special wave")
        mobs = []
        for mob, i in self.special_waves[name].items():
            mobs.extend([mob] * i)
        random.shuffle(mobs)
        return mobs

    def next_wave(self) -> list[str]:
        """
        Returns a list of mobs that should appear in the current wave.
        This automatically goes to the next wave, raising a RuntimeError when
        waves are exhausted.

        :raises RuntimeError: There are no more waves left.
        :return: A list of mob names to appear in the next wave.
        :rtype: list[str]
        """
        if self.current_wave > self.last_wave:
            raise RuntimeError(
                "There are no more waves defined for this level."
            )
        wave = self.waves[self.current_wave]
        if isinstance(wave[0], str):
            dist = self._get_special_wave_distribution(self.current_wave)
        else:
            dist = self._calculate_wave_distribution(self.current_wave)
        self.current_wave += 1
        return dist


class Upgrade:
    def __init__(self, level: int = 0) -> None:
        self.level = level

    def upgrade(self) -> int:
        """Upgrade and return new level."""
        self.level += 1
        return self.level


class ResurrectionCoin:
    TEXTURE = TEXTURES_PATH.get("res_coin")


class Item:
    RARE: bool
    DURATION: int | float
    TEXTURE: Path

    def __init__(self) -> None:
        self.time_used: Optional[float] = None

    def use(self) -> None:
        self.time_used = time.time()


class SemiAutomatic(Item):
    RARE = False
    DURATION = 12
    FIRE_RATE = 10
    TEXTURE = TEXTURES_PATH.get("semi_automatic")


class Pressurer(Item):
    RARE = True
    DURATION = 12
    BULLET_SPEED_MOD = 1.5
    DAMAGE_MOD = 2.0
    TEXTURE = TEXTURES_PATH.get("pressurer")


class Scope(Item):
    RARE = False
    DURATION = 18
    EXTRA_PENETRATION = 1
    FIRE_RATE_MOD = 0.8
    TEXTURE = TEXTURES_PATH.get("scope")


class BlueCow(Item):
    RARE = False
    DURATION = 15
    SPEED_MOD = 1.35
    TEXTURE = TEXTURES_PATH.get("blue_cow")


class Spray(Item):
    RARE = False
    DURATION = 13
    TEXTURE = TEXTURES_PATH.get("spray")


class ThreeSixty(Item):
    RARE = False
    DURATION = 12
    TEXTURE = TEXTURES_PATH.get("three_sixty")


class HolyGuard(Item):
    RARE = True
    DURATION = 8
    IMMUNITY_DURATION = 3
    TEXTURE = TEXTURES_PATH.get("holy_guard")


class SmokeBomb(Item):
    RARE = True
    DURATION = 7
    TEXTURE = TEXTURES_PATH.get("smoke_bomb")


class LaserBeam(Item):
    RARE = True
    DURATION = 15
    SECONDS_PER_CYCLE = 1.5
    RANGE = 3
    DAMAGE = 8
    TEXTURE = TEXTURES_PATH.get("laser_beam")


class Bullet(Sprite):  # type: ignore[misc]
    def __init__(
        self,
        damage: int = 1,
        penetration: int = 0,
        path_or_texture: cme.types.PathOrTexture = None,
        scale: float = 1.0,
        center_x: float = 0.0,
        center_y: float = 0.0,
        angle: float = 0.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            path_or_texture=path_or_texture,
            scale=scale,
            center_x=center_x,
            center_y=center_y,
            angle=angle,
            **kwargs
        )
        self.damage = damage
        self.remaining_penetration = penetration
        self.hostiles_hit = SpriteList()  # Avoid hitting an enemy twice


class Hostile(AnimatedSprite):  # type: ignore[misc]
    HP: int
    BASE_SPEED: float

    def __init__(
        self,
        player: Sprite,
        walls: SpriteList,
        hostiles: SpriteList,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.player = player
        self.walls = walls
        self.other_hostiles = SpriteList()
        for hostile in hostiles:
            if hostile != self:
                self.other_hostiles.append(hostile)
        self.hp = self.HP
        self.can_attack = True
        self.last_attack = 0.0
        self.player_moved = True
        self.attack_cooldown = 0.0
        self.next_point: Optional[types.Point] = None
        self.path_queue: Optional[deque[types.Point]] = None
        self.path_pending = False
        self.pending_path_queue: Optional[multiprocessing.pool.AsyncResult[Any]] = None  # noqa
        self.path_calc_process: Optional[Process] = None

    @property
    def speed(self) -> float:
        return self.BASE_SPEED

    def on_update(self, delta_time: float) -> None:
        super().on_update(
            delta_time,
            SimpleUpdater(),
        )

        if self.path_pending and self.pending_path_queue.ready():  # type: ignore[union-attr]  # noqa
            self.path_pending = False
            self._process_path(self.pending_path_queue.get())  # type: ignore

        if any([self.player.change_x, self.player.change_y]):
            self.player_moved = True
        else:
            self.player_moved = False

        if (
            self.can_attack
            and time.time() - self.last_attack >= self.attack_cooldown
        ):
            self.attack()
            self.last_attack = time.time()

        if self.next_point:
            at_point_x = False
            at_point_y = False
            if abs(self.center_x - self.next_point[0]) <= abs(  # type: ignore[has-type]  # noqa
                self.change_x * delta_time  # type: ignore[has-type]
            ):
                self.center_x = self.next_point[0]
                self.change_x = 0
                at_point_x = True
            if abs(self.center_y - self.next_point[1]) <= abs(  # type: ignore[has-type]  # noqa
                self.change_y * delta_time  # type: ignore[has-type]
            ):
                self.center_y = self.next_point[1]
                self.change_y = 0
                at_point_y = True
            if all([at_point_x, at_point_y]):
                self.next_point = None

        if self.next_point is None and self.path_queue:
            self.next_point = self.path_queue.pop()
            angle = cme.utils.calc_angle(self.center, self.next_point)
            self.change_x, self.change_y = cme.utils.calc_change_x_y(
                speed(self.speed), angle
            )

    def _walk_to_point(self, point: types.Point) -> None:
        if self.path_pending:
            return
        self.path_pending = True
        self.pending_path_queue = enqueue_pathfinder(self, point, self.walls)

    def _process_path(self, path: list[types.Point]) -> None:
        if path is not None:
            self.path_queue = deque(reversed(path))
            if self.next_point:
                # We don't want to take the first step when we are walking
                # already, as sprite would go back and forth
                self.path_queue.pop()

    def _walk_to_player(self) -> None:
        if not self.path_queue or self.player_moved:
            self._walk_to_point((self.player.center_x, self.player.center_y))

    def attack(self) -> None:
        raise NotImplementedError


class Zombie(Hostile):
    """Slow creature with low health. Kills on collision."""
    HP = 1
    BASE_SPEED = 0.5

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.attack_cooldown = 0.6
        self.add_texture(
            load_texture(TEXTURES_PATH.get("zombie_default.png")), "idling"
        )
        self.state = "idling"

    def attack(self) -> None:
        self._walk_to_player()


class Player(AnimatedWalkingSprite):  # type: ignore[misc]
    BASE_DAMAGE = 1
    BASE_SPEED = 1
    BASE_FIRE_RATE = 3
    BASE_BULLET_SPEED = 2

    def __init__(self, *args: Any, **kwargs: Any) -> None:
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
        self.can_move = True

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
        else:  # self.change_x < 0 and self.change_y > 0
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
            self.change_y = dir_vertical * speed(self.final_movement_speed)  # type: ignore[assignment]  # noqa
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

        if self.can_move:
            super().on_update(
                delta_time, TopDownUpdater(
                    self.walls, types.LBWH(0, 0, MAP_SIZE, MAP_SIZE)
                )
            )

        # Set facing by walk direction
        self.facing_angle = self.calc_facing_angle()

        # Remove timed out items
        cur_time = time.time()
        for item in self.active_items.copy():
            if item.time_used < cur_time - item.DURATION:  # type: ignore[operator]  # noqa
                self.active_items.remove(item)

    def use_item(self) -> None:
        if not self.stored_item:
            return

        self._use_item(self.stored_item)
        self.stored_item = None

    def pickup_item(self, item: Item) -> None:
        if not self.stored_item:
            self.stored_item = item
        else:
            # Auto use
            self._use_item(item)

    def _use_item(self, item: Item) -> None:
        # Only one item of a type can be active at once
        for active_item in self.active_items.copy():
            if isinstance(active_item, item.__class__):
                self.active_items.remove(active_item)

        self.active_items.append(item)
        item.use()

    def shoot(self) -> Optional[list[Sprite]]:
        """
        Create and move bullet sprites. Returns a list of bullets to be added
        to the scene, or None, if the player can't shoot at the moment.

        :return: A list of bullet sprites to be added to the scene object. None
        if the shooting cooldown isn't over yet.
        :rtype: Optional[list[Sprite]]
        """
        if self.last_shot > time.time() - 1 / self.final_fire_rate:
            return None  # Can't shoot that fast

        if not self.can_move:
            return None

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
            return None
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

        bullets: list[Sprite] = []
        bullet_speed = self.final_bullet_speed
        bullet_damage = self.final_damage
        bullet_penetration = self.final_penetration

        if find_with_class(
            self.active_items, Spray
        ) and not find_with_class(
            self.active_items, ThreeSixty
        ):
            for angle in (
                shoot_angle - 22.5,
                # We don't want the middle as it's added anyways
                shoot_angle + 22.5,
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

        if find_with_class(
            self.active_items, ThreeSixty
        ) and not find_with_class(
            self.active_items, Spray
        ):
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

        if find_with_class(
            self.active_items, ThreeSixty
        ) and find_with_class(
            self.active_items, Spray
        ):
            for angle in (
                # We don't want the middle as it's added anyways
                shoot_angle + 22.5,
                shoot_angle + 45,
                shoot_angle + 67.5,
                shoot_angle + 90,
                shoot_angle + 112.5,
                shoot_angle + 135,
                shoot_angle + 157.5,
                shoot_angle + 180,
                shoot_angle + 202.5,
                shoot_angle + 225,
                shoot_angle + 247.5,
                shoot_angle + 270,
                shoot_angle + 292.5,
                shoot_angle + 315,
                shoot_angle + 337.5,
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
    def final_damage(self) -> int:
        """
        Get the damage done with a single shot, taking ammo and items into
        account.
        """
        damage = self.BASE_DAMAGE + self.BASE_DAMAGE * 0.5 * self.ammo.level
        if item := find_with_class(self.active_items, Pressurer):
            damage *= item.DAMAGE_MOD
        return math.floor(damage)

    @property
    def final_fire_rate(self) -> float:
        """Get the gun's fire rate, taking gun level and items into account."""
        rate = self.BASE_FIRE_RATE + self.BASE_FIRE_RATE * 0.2 * self.gun.level
        if item := find_with_class(self.active_items, SemiAutomatic):
            rate = item.FIRE_RATE
        if item := find_with_class(self.active_items, Scope):
            rate *= item.FIRE_RATE_MOD
        return rate

    @property
    def final_penetration(self) -> int:
        """
        Get the gun's penetration, taking gun level and items into account.
        """
        penetration = max(int(1 * 0.5 * self.gun.level), 1)
        if item := find_with_class(self.active_items, Scope):
            penetration += item.EXTRA_PENETRATION
        return penetration

    @property
    def final_movement_speed(self) -> float:
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
    def final_bullet_speed(self) -> float:
        """Get bullet speed, taking items into account."""
        speed = self.BASE_BULLET_SPEED
        if item := find_with_class(self.active_items, Pressurer):
            speed *= item.BULLET_SPEED_MOD
        return speed


class Triangle(Sprite):  # type: ignore[misc]
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time, WallBounceUpdater(
            types.LBWH(
                0, 0,
                cme.get_window().width,
                cme.get_window().height,
            )
        ))


MOB_NAME_TO_MOB = {
    "zombie": Zombie,
    # "giant": Giant,
    # "mosquito": Mosquito,
    # "fire_zombie": FireZombie,
    # "fire_atronach": FireAtronach,
    # "hellcrab": Hellcrab,
    # "fire_spirit": FireSpirit,
    # "blaze": Blaze,
    # "rotten_soul": RottenSoul,
    # "mummy": Mummy,
    # "skeleton_puppy": SkeletonPuppy,
    # "soul_sniper": SoulSniper,
    # "soul_crawler": SoulCrawler,
    # "haunted_spectre": HauntedSpectre,
    # "illuminati_mage": IlluminatiMage,
    # "illuminati_sniper": IlluminatiSniper,
    # "illuminati_striker": IlluminatiStriker,
    # "illuminati_summoner": IlluminatiSummoner,
    # "illuminati_inferno": IlluminatiInferno,
    # "mean_illuminati": MeanIlluminati,
    # "dwarf_trio": DwarfTrio,
    # "blaze_queen": BlazeQueen,
    # "ghost_pirate_jake": GhostPirateJake,
    # "delta": Delta,
}

ITEMS: list[type[Item]] = [
    SemiAutomatic, Pressurer, Scope, BlueCow, Spray,
    ThreeSixty, HolyGuard, SmokeBomb, LaserBeam,
]
