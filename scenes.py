from game_collections import *
import game_constants as c
import typing as _typing
from game_objects import *
import pygame
import os
from random import choice, randint


class MapGenerator(ListenerLike):
    def __init__(
        self,
        *,
        listen_receivers: _typing.Optional[_typing.Set[str]] = None,
        width,
        height,
        map_tile_width=16,
        map_tile_height=16,
        scale,
        path,
        core,
        player,
        enemy_amount,
        obstacle_amount,
    ):
        super().__init__(post_api=core.add_event, listen_receivers=listen_receivers)
        self.__path = path
        self.player = player
        self.width = width
        self.height = height
        self.map_tile_width = map_tile_width
        self.map_tile_height = map_tile_height
        self.core = core
        self.enemy_amount = enemy_amount
        self.obstacle_amount = obstacle_amount
        self.__floors = os.listdir(os.path.join(path, "floors/"))
        self.__walls = os.listdir(os.path.join(path, "walls/"))
        self.__obstacles = os.listdir(os.path.join(path, "obstacles/"))
        self.scale = scale

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, new_path):
        self.__path = new_path
        self.__floors = os.listdir(os.path.join(new_path, "floors/"))
        self.__walls = os.listdir(os.path.join(new_path, "walls/"))
        self.__obstacles = os.listdir(os.path.join(new_path, "obstacles/"))

    def generate_random_battle_ground(self, enemy_list: list):
        scene = SceneLike(
            self.core,
            mapsize=(
                self.width * self.map_tile_width * self.scale,
                self.height * self.map_tile_height * self.scale,
            ),
            name="battleground",
            player=self.player,
        )
        for i in range(self.width):
            for j in range(self.height):
                print("generating", i, j)
                if i == 0 or j == 0 or i == self.width - 1 or j == self.height - 1:
                    image = pygame.image.load(
                        os.path.join(self.__path, "walls/", choice(self.__walls))
                    )
                    image = pygame.transform.scale(
                        image,
                        (
                            image.get_width() * self.scale,
                            image.get_height() * self.scale,
                        ),
                    )
                    wall = Tile(self.core.add_event, image)
                    wall.tile_cord = (i, j)
                    scene.add_listener(wall, 0, True)
                else:
                    image = pygame.image.load(
                        os.path.join(self.__path, "floors/", choice(self.__floors))
                    )
                    image = pygame.transform.scale(
                        image,
                        (
                            image.get_width() * self.scale,
                            image.get_height() * self.scale,
                        ),
                    )
                    floor = Tile(self.core.add_event, image)
                    floor.tile_cord = (i, j)
                    scene.add_listener(floor, 0)
        for i in range(self.obstacle_amount):
            image = pygame.image.load(
                os.path.join(self.__path, "obstacles/", choice(self.__obstacles))
            )
            image = pygame.transform.scale(
                image,
                (
                    image.get_width() * self.scale,
                    image.get_height() * self.scale,
                ),
            )
            obstacle = EntityLike(
                image=image, rect=image.get_rect(), post_api=self.core.add_event
            )
            # 不断尝试，直到生成一个不会和别的东西碰撞的坐标，不要有太多障碍，或者地图太小，可能会死循环
            x = randint(
                self.map_tile_width * self.scale + 1,
                scene.map_height
                - self.map_tile_width * self.scale
                - obstacle.rect.width,
            )
            y = randint(int(scene.map_height * 0.2), int(scene.map_height * 0.8))

            obstacle.rect.move_ip(x, y)
            while obstacle.rect.collidelist([wall.rect for wall in scene.walls]) != -1:
                x = randint(
                    self.map_tile_width * self.scale + 1,
                    scene.map_height
                    - self.map_tile_width * self.scale
                    - obstacle.rect.width,
                )
                y = randint(int(scene.map_height * 0.2), int(scene.map_height * 0.8))
                obstacle.rect.move_ip(x, y)

            scene.add_listener(obstacle, 1, True)
        for i in range(self.enemy_amount):
            enemy = choice(enemy_list).create_self(self.core.add_event)
            enemy.target = self.player
            x = randint(
                self.map_tile_width * self.scale + 1,
                scene.map_height - self.map_tile_width * self.scale - enemy.rect.width,
            )
            y = randint(int(scene.map_height * 0.2), int(scene.map_height * 0.8))

            enemy.rect.move_ip(x, y)
            while enemy.rect.collidelist([wall.rect for wall in scene.walls]) != -1:
                x = randint(
                    self.map_tile_width * self.scale + 1,
                    scene.map_height
                    - self.map_tile_width * self.scale
                    - enemy.rect.width,
                )
                y = randint(int(scene.map_height * 0.2), int(scene.map_height * 0.8))
                enemy.rect.move_ip(x, y)
            scene.add_listener(enemy, 3)
            # 说明地图在一层，障碍在二层，怪在三层，player在四层
        self.player.rect.centerx = scene.map_width // 2
        self.player.rect.centery = scene.map_height - 120
        scene.add_listener(self.player, 4)
        scene.update_camera_by_chara(scene.player)
        return scene


class Home(SceneLike):
    def __init__(
        self,
        core: Core,
        *,
        listen_receivers: Optional[Set[str]] = None,
        post_api: Optional[PostEventApiLike] = None,
        mapsize=(3000, 2000),
        name="home",
        player=None,
    ):
        super().__init__(
            core,
            listen_receivers=listen_receivers,
            post_api=post_api,
            mapsize=mapsize,
            name=name,
            player=player,
        )
        self.load_tilemap("./maps/1.json")
        self.add_listener(self.player, 3)
        self.update_camera_by_chara(self.player)
