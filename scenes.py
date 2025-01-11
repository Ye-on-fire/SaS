from pydantic.types import T
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
        map_tile_width=16,
        map_tile_height=16,
        scale,
        core,
        player,
    ):
        super().__init__(post_api=core.add_event, listen_receivers=listen_receivers)
        self.player = player
        self.map_tile_width = map_tile_width
        self.map_tile_height = map_tile_height
        self.core = core
        self.scale = scale
        self.__walls = [[] for i in range(8)]
        self.level = 0

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
        self.enemy_amount = 1 + int(new_level * 0.8)
        self.enemy_damage = 10 + int(new_level * 1.5)
        self.enemy_hp = 30 + int(new_level * 2)
        self.enemy_moneydrop = 10 + int(new_level * 4)

    def generate_boss(self):
        self.path = "./assets/mytiles/dungeon/"
        self.width = 30
        self.height = 20
        self.obstacle_amount = 0
        self.enemy_amount = 0
        scene = self.generate_random_battle_ground([Skeleton], boss_flag=True)
        boss = Boss(post_api=self.post_api, target=self.player)
        scene.add_listener(boss, 3)
        return scene

    def generate_random_battle_ground(self, enemy_list: list, boss_flag=False):
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
            enemy = choice(enemy_list).create_self(
                self.core.add_event,
                self.enemy_hp,
                self.enemy_damage,
                randint(self.enemy_moneydrop - 5, self.enemy_moneydrop + 5),
            )
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
        if not boss_flag:
            door = Door(self.post_api)
            door.rect.centerx = scene.map_width // 2
            door.rect.top = self.map_tile_height
            scene.add_listener(door, 2)
            if self.level % 3 == 0:
                bonfire = BonfireDoor(self.post_api)
                bonfire.rect.centerx = scene.map_width * 0.7
                bonfire.rect.top = self.map_tile_height
                scene.add_listener(bonfire, 2)
        return scene


class Home(SceneLike):
    def __init__(
        self,
        core: Core,
        *,
        listen_receivers: Optional[Set[str]] = None,
        mapsize=(3000, 2000),
        name="home",
        player=None,
        resourcemanager,
    ):
        super().__init__(
            core,
            listen_receivers=listen_receivers,
            post_api=core.add_event,
            mapsize=mapsize,
            name=name,
            player=player,
        )
        self.load_tilemap("./maps/1.json")
        self.npc = Tutor(self.player, self.post_api)
        self.npc.rect.move_ip(100, 400)
        self.bonfire = Bonfire(self.post_api, self.player, resourcemanager)
        self.bonfire.rect.move_ip(500, 500)
        self.healer = Healer(self.player, self.post_api)
        self.healer.rect.move_ip(800, 400)
        self.add_listener(self.bonfire, 2)
        self.add_listener(self.npc, 3)
        self.add_listener(self.healer, 3)
        self.add_listener(self.player, 4)
        self.update_camera_by_chara(self.player)


class MainMenu(SceneLike):
    def __init__(self, core, mapsize=(1280, 720), name="mainmenu", player=None):
        super().__init__(
            core, post_api=core.add_event, mapsize=mapsize, name=name, player=player
        )
        self.bg_image = load_image_and_scale(
            "./assets/background/mainmenu.jpg", pygame.Rect(0, 0, 1280, 720)
        )

    @listening(c.EventCode.DRAW)
    def draw(self, event):
        surface = event.body["window"]
        surface.blit(self.bg_image, (0, 0))

    @listening(pygame.KEYDOWN)
    def on_keydown(self, event):
        Core.play_music("./assets/bgm/home.mp3")
        self.post(EventLike(c.SceneEventCode.CHANGE_SCENE, body={"scene_name": "home"}))


class GameOver(SceneLike):
    def __init__(self, core, mapsize=(1280, 720), name="gameover", player=None):
        super().__init__(
            core, post_api=core.add_event, mapsize=mapsize, name=name, player=player
        )
        self.bg_image = load_image_and_scale(
            "./assets/background/gameover.jpg", pygame.Rect(0, 0, 1280, 720)
        )

    @listening(c.EventCode.DRAW)
    def draw(self, event):
        surface = event.body["window"]
        surface.blit(self.bg_image, (0, 0))

    @listening(pygame.KEYDOWN)
    def on_keydown(self, event):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            print("restart")
            self.post(EventLike(c.EventCode.GAME_RESTART))
        elif keys[pygame.K_ESCAPE]:
            self.core.exit()


class Victory(SceneLike):
    def __init__(self, core, mapsize=(1280, 720), name="victory", player=None):
        super().__init__(
            core, post_api=core.add_event, mapsize=mapsize, name=name, player=player
        )
        self.bg_image = load_image_and_scale(
            "./assets/background/victory.png", pygame.Rect(0, 0, 1280, 720)
        )

    @listening(c.EventCode.DRAW)
    def draw(self, event):
        surface = event.body["window"]
        surface.blit(self.bg_image, (0, 0))

    @listening(pygame.KEYDOWN)
    def on_keydown(self, event):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            print("restart")
            self.post(EventLike(c.EventCode.GAME_RESTART))
        elif keys[pygame.K_ESCAPE]:
            self.core.exit()


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


class BonfireDoor(EntityLike):
    def __init__(self, post_api=None, listen_receivers: Optional[Set[str]] = None):
        self.closed_image = load_image_and_scale(
            "./assets/mytiles/closed_bonfire.png", pygame.Rect(0, 0, 80, 100)
        )
        self.open_image = load_image_and_scale(
            "./assets/mytiles/open_bonfire.png", pygame.Rect(0, 0, 80, 100)
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
            self.post(
                EventLike(
                    c.MoveEventCode.MOVEALLOW,
                    body={"pos": pygame.Rect(500, 500, 63, 114)},
                )
            )
            Core.play_music("./assets/bgm/home.mp3")
            self.post(
                EventLike(c.SceneEventCode.CHANGE_SCENE, body={"scene_name": "home"})
            )


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
        if self.mapgenerator.level <= 10:
            self.mapgenerator.level += 1
            self.__scene_list["battleground"] = (
                self.mapgenerator.generate_random_battle_ground([Skeleton])
            )
            self.current_scene = self.__scene_list["battleground"]
        else:
            Core.play_music("./assets/bgm/boss.mp3")
            self.post(
                EventLike(c.SceneEventCode.CHANGE_SCENE, body={"scene_name": "boss"})
            )
