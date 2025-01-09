from cmath import rect
from struct import calcsize
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
    ):
        super().__init__(post_api=core.add_event, listen_receivers=listen_receivers)
        self.__path = path
        self.player = player
        self.width = width
        self.height = height
        self.map_tile_width = map_tile_width
        self.map_tile_height = map_tile_height
        self.core = core
        self.__floors = os.listdir(os.path.join(path, "floors/"))
        self.__walls = [[] for i in range(8)]
        # wall有8种，分别是4个角上的和4个边上的topleft:0,topright:1,bottomleft:2,bottomright:3,left:4,top:5,right:6,bottom:7
        self.__walls[0] = os.listdir(os.path.join(path, "walls/topleft/"))
        self.__walls[1] = os.listdir(os.path.join(path, "walls/topright/"))
        self.__walls[2] = os.listdir(os.path.join(path, "walls/bottomleft/"))
        self.__walls[3] = os.listdir(os.path.join(path, "walls/bottomright/"))
        self.__walls[4] = os.listdir(os.path.join(path, "walls/left/"))
        self.__walls[5] = os.listdir(os.path.join(path, "walls/top/"))
        self.__walls[6] = os.listdir(os.path.join(path, "walls/right/"))
        self.__walls[7] = os.listdir(os.path.join(path, "walls/bottom/"))
        self.__obstacles = os.listdir(os.path.join(path, "obstacles/"))
        self.scale = scale
        self.level = 1

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, new_path):
        self.__path = new_path
        self.__floors = os.listdir(os.path.join(new_path, "floors/"))
        self.__walls[0] = os.listdir(os.path.join(new_path, "walls/topleft/"))
        self.__walls[1] = os.listdir(os.path.join(new_path, "walls/topright/"))
        self.__walls[2] = os.listdir(os.path.join(new_path, "walls/bottomleft/"))
        self.__walls[3] = os.listdir(os.path.join(new_path, "walls/bottomright/"))
        self.__walls[4] = os.listdir(os.path.join(new_path, "walls/left/"))
        self.__walls[5] = os.listdir(os.path.join(new_path, "walls/top/"))
        self.__walls[6] = os.listdir(os.path.join(new_path, "walls/right/"))
        self.__walls[7] = os.listdir(os.path.join(new_path, "walls/bottom/"))
        self.__obstacles = os.listdir(os.path.join(new_path, "obstacles/"))

    @property
    def level(self):
        # 这是一个用来操控地图生成难度的量(做10关的话就是1-10)
        return self.__level

    @level.setter
    def level(self, new_level):
        self.__level = new_level
        if new_level <= 5:
            self.path = "./assets/mytiles/grassland/"
        else:
            self.path = "./assets/mytiles/dungeon/"
        self.width = 30 + new_level * 2
        self.height = 20 + new_level * 2
        self.obstacle_amount = int(new_level * 0.6)
        self.enemy_amount = 1 + int(new_level * 1.2)

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
                if i == 0 and j == 0:
                    image = pygame.image.load(
                        os.path.join(
                            self.__path, "walls/topleft", choice(self.__walls[0])
                        )
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
                elif i == self.width - 1 and j == 0:
                    image = pygame.image.load(
                        os.path.join(
                            self.__path, "walls/topright", choice(self.__walls[1])
                        )
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
                elif i == 0 and j == self.height - 1:
                    image = pygame.image.load(
                        os.path.join(
                            self.__path, "walls/bottomleft", choice(self.__walls[2])
                        )
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
                elif i == self.width - 1 and j == self.height - 1:
                    image = pygame.image.load(
                        os.path.join(
                            self.__path, "walls/bottomright", choice(self.__walls[3])
                        )
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
                elif i == 0:
                    image = pygame.image.load(
                        os.path.join(self.__path, "walls/left", choice(self.__walls[4]))
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
                elif j == 0:
                    image = pygame.image.load(
                        os.path.join(self.__path, "walls/top", choice(self.__walls[5]))
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
                elif i == self.width - 1:
                    image = pygame.image.load(
                        os.path.join(
                            self.__path, "walls/right", choice(self.__walls[6])
                        )
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
                elif j == self.height - 1:
                    image = pygame.image.load(
                        os.path.join(
                            self.__path, "walls/bottom", choice(self.__walls[7])
                        )
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
                scene.map_width
                - self.map_tile_width * self.scale
                - obstacle.rect.width,
            )
            y = randint(int(scene.map_height * 0.2), int(scene.map_height * 0.7))

            obstacle.rect.x = x
            obstacle.rect.y = y
            while obstacle.rect.collidelist([wall.rect for wall in scene.walls]) != -1:
                print("loop1")
                x = randint(
                    self.map_tile_width * self.scale + 1,
                    scene.map_width
                    - self.map_tile_width * self.scale
                    - obstacle.rect.width,
                )
                y = randint(int(scene.map_height * 0.2), int(scene.map_height * 0.7))
                obstacle.rect.x = x
                obstacle.rect.y = y

            scene.add_listener(obstacle, 1, True)
        print("scene:", scene.map_width, scene.map_height)
        for i in range(self.enemy_amount):
            enemy = choice(enemy_list).create_self(self.core.add_event)
            enemy.target = self.player
            x = randint(
                self.map_tile_width * self.scale + 10,
                scene.map_width
                - self.map_tile_width * self.scale
                - enemy.rect.width
                - 50,
            )
            y = randint(int(scene.map_height * 0.2), int(scene.map_height * 0.7))
            print(x, y)
            enemy.rect.x = x
            enemy.rect.y = y
            while enemy.rect.collidelist([wall.rect for wall in scene.walls]) != -1:
                print("loop2")
                x = randint(
                    self.map_tile_width * self.scale + 10,
                    scene.map_width
                    - self.map_tile_width * self.scale
                    - enemy.rect.width
                    - 50,
                )
                y = randint(int(scene.map_height * 0.2), int(scene.map_height * 0.7))
                print(x, y)
                enemy.rect.x = x
                enemy.rect.y = y
            scene.add_listener(enemy, 3)
            # 说明地图在一层，障碍在二层，怪在三层，player在四层
        self.player.rect.centerx = scene.map_width // 2
        self.player.rect.centery = scene.map_height - 120
        scene.add_listener(self.player, 4)
        scene.update_camera_by_chara(scene.player)
        door = Door(self.post_api)
        door.rect.centerx = scene.map_width // 2
        door.rect.top = self.map_tile_height
        scene.add_listener(door, 4)
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


class Door(EntityLike):
    def __init__(self, post_api=None, listen_receivers: Optional[Set[str]] = None):
        self.closed_image = load_image_and_scale(
            "./assets/mytiles/closed_door.png", pygame.Rect(0, 0, 80, 100)
        )
        self.open_image = load_image_and_scale(
            "./assets/mytiles/open_door.png", pygame.Rect(0, 0, 80, 100)
        )
        rect = self.open_image.get_rect()
        super().__init__(
            rect,
            image=self.closed_image,
            post_api=post_api,
            listen_receivers=listen_receivers,
        )
        self.opened = False

    @listening(c.SceneEventCode.DOOR_OPEN)
    def door_open(self, event):
        self.image = self.open_image
        self.opened = True

    @listening(c.MoveEventCode.MOVEATTEMPT)
    def judge_move(self, event):
        if self.opened and event.body["original_pos"].move(
            event.body["move_offset"]
        ).colliderect(self.rect):
            self.post(EventLike(c.SceneEventCode.NEW_LEVEL))


class SceneManager(ListenerLike):
    # 用来管理场景和切换场景
    def __init__(
        self, post_api, scenelist, inital_scene_name, mapgenerator: MapGenerator
    ):
        super().__init__(post_api=post_api)
        self.__scene_list = scenelist
        self.current_scene = self.__scene_list[inital_scene_name]
        self.mapgenerator = mapgenerator

    def add_scene(self, scene: SceneLike):
        self.__scene_list[scene.name] = scene

    def listen(self, event):
        super().listen(event)
        self.current_scene.listen(event)

    @listening(c.SceneEventCode.CHANGE_SCENE)
    def change_scene(self, event):
        if event.body["scene_name"] in self.__scene_list.keys():
            self.current_scene = self.__scene_list[event.body["scene_name"]]
            self.current_scene.player.rect.x = event.body["playerpos"][0]
            self.current_scene.player.rect.y = event.body["playerpos"][1]
            self.current_scene.update_camera_by_chara(self.current_scene.player)
        else:
            print("no such scene")

    @listening(c.SceneEventCode.RESTART)
    def restart_scene(self, event):
        self.__scene_list[event.body["scene_name"]] = event.body["pre_loaded_scene"]
        # self.current_scene.update_camera_by_chara(self.current_scene.player)
        self.current_scene = self.__scene_list[event.body["scene_name"]]

    @listening(c.SceneEventCode.NEW_LEVEL)
    def create_new_level(self, event):
        self.mapgenerator.level += 1
        self.__scene_list["battleground"] = (
            self.mapgenerator.generate_random_battle_ground([Skeleton])
        )
        self.current_scene = self.__scene_list["battleground"]
