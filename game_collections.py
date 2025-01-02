from dis import pretty_flags
from hmac import new
import json
from pdb import post_mortem
from typing import (
    List,
    Dict,
    Tuple,
    Set,
    Optional,
    Set,
    Any,
)
import collections

import pygame
from loguru import logger

import os
import game_constants as c
from base import (
    EventLike,
    ListenerLike,
    GroupLike,
    Core,
    PostEventApiLike,
    listening,
)


class EntityLike(ListenerLike, pygame.sprite.Sprite):
    """
    表示游戏框架内的实体类, 继承了 `pygame.sprite.Sprite`。
    提供`image`, `mask`, `rect`属性。

    Attributes
    ---
    mask : pygame.Mask:
        返回图像的掩码, 用于碰撞检测
    rect : pygame.Rect
        实体的矩形区域, 用于定位和碰撞检测
    image : pygame.Surface
        实体图像

    Methods
    -------
    draw@DRAW
        在屏幕上绘制实体。
    """

    # attributes
    rect: pygame.Rect
    __image: Optional[pygame.Surface]

    @property
    def mask(self) -> pygame.Mask:
        """
        返回图像的掩码, 用于碰撞检测

        Returns
        -------
        pygame.Mask

        Notes
        ---
        此变量根据`self.image`生成, 不可修改
        """
        return pygame.mask.from_surface(self.image)

    @property
    def image(self) -> pygame.Surface:
        """
        实体图像。

        如果`self.__image`为None, 则返回`self.rect`大小的完全透明图像。

        Returns
        -------
        pygame.Surface
        """
        if self.__image is None:
            return pygame.Surface(self.rect.size, pygame.SRCALPHA)
        return self.__image

    @image.setter
    def image(self, image: Optional[pygame.Surface]):
        self.__image = image

    def __init__(
        self,
        rect: pygame.Rect,
        *,
        image: Optional[pygame.Surface] = None,
        post_api: Optional[PostEventApiLike] = None,
        listen_receivers: Optional[Set[str]] = None,
    ):
        """
        Parameters
        ---
        rect : pygame.Rect
            实体的矩形区域, 用于定位和碰撞检测
        image : Optional[pygame.Surface], optional, default = None
            实体图像, 传入None则会被视作`rect`大小的完全透明图像。
        post_api : (EventLike) -> None, optional, default = None
            发布事件函数, 一般使用`Core`的`add_event`
        listen_receivers : set[str], optional, default = {EVERYONE_RECEIVER, self.uuid}
            监听的接收者集合, 自动加上EVERYONE_RECEIVER与self.uuid
        """
        super().__init__(post_api=post_api, listen_receivers=listen_receivers)
        pygame.sprite.Sprite.__init__(self)

        self.rect: pygame.Rect = rect
        self.__image: Optional[pygame.Surface] = image

    @listening(c.EventCode.DRAW)
    def draw(self, event: EventLike):
        """
        在画布上绘制实体

        Listening
        ---
        DRAW : DrawEventBody
            window : pygame.Surface
                画布
            camera : tuple[int, int]
                镜头坐标（/负偏移量）
        """
        body: c.DrawEventBody = event.body
        window: pygame.Surface = body["window"]
        camera: Tuple[int, int] = body["camera"]

        rect = self.rect.move(*(-i for i in camera))
        if self.image is not None:
            window.blit(self.image, rect)


def generate_imageset(path):
    imageset = {}
    for i in os.listdir(path):
        temp = [[], []]
        for j in sorted(os.listdir(os.path.join(path, i))):
            image = pygame.image.load(os.path.join(path, i, j))
            print(f"loaded{os.path.join(path, i, j)}")
            image = pygame.transform.scale(
                image, (image.get_width() * 3, image.get_height() * 3)
            )
            image_left = pygame.transform.flip(image, 1, 0)
            temp[0].append(image)
            temp[1].append(image_left)
        imageset[i] = temp
    return imageset


def generate_imageset_for_mac(path):
    imageset = {}
    for i in os.listdir(path):
        if i != ".DS_Store":
            temp = [[], []]
            for j in sorted(os.listdir(os.path.join(path, i))):
                if j != ".DS_Store":
                    image = pygame.image.load(os.path.join(path, i, j))
                    print(f"loaded{os.path.join(path, i, j)}")
                    image = pygame.transform.scale(
                        image, (image.get_width() * 3, image.get_height() * 3)
                    )
                    image_left = pygame.transform.flip(image, 1, 0)
                    temp[0].append(image)
                    temp[1].append(image_left)
                imageset[i] = temp
    return imageset


class State:
    """
    State类
    主要管理动画和角色的状态
    name：状态类型
    can_be_changed：动画能不能在播放中间被打断（取消）一般循环的动画都是可打断的
    is_loop：关于这个动画是循环的还是只播放一次
    duration:动画两帧之间需要间隔几帧
    info:各种杂七杂八的东西，比如记录每一帧角色的状态
        frame_type:0 normal 1 attack 2 invincible 3
    """

    def __init__(
        self,
        name: str,
        change_flag=True,
        loop_flag=True,
        info: dict = {},
        duration=1,
        prior_flag=False,
    ) -> None:
        self.name = name
        self.can_be_changed = change_flag
        self.is_loop = loop_flag
        self.duration = duration
        self.high_priority = prior_flag
        self.info = info

    @classmethod
    def create_idle(cls):
        info = {"can_move": True}
        return cls("idle", duration=15, info=info)

    @classmethod
    def create_run(cls):
        info = {"can_move": True}
        return cls("run", duration=5, info=info)

    @classmethod
    def create_attack(cls):
        info = {"frame_type": [0, 0, 1, 0, 0, 0], "can_move": False}
        return cls("attack", change_flag=False, loop_flag=False, duration=5, info=info)

    @classmethod
    def create_roll(cls):
        info = {"frame_type": [0, 0, 0, 2, 2, 2, 2, 2, 2, 0, 0, 0], "can_move": True}
        return cls("roll", change_flag=False, loop_flag=False, duration=3, info=info)

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name


class AnimatedSprite(EntityLike):
    """
    有动画的角色的基类
    包含一个imageset，储存了该角色所有的动画
    和一个state，用来管理该角色的动画和行为
    direction是该角色的方向
    定义的时候应该要传入一个该角色开始的图片和状态
    默认为idle，图片为idle的第一帧
    关于创建动画：第一步，将动画图片重命名为01，02……放在角色该动作的文件夹下
    第二部，为该动画创建一个State类型
    第三部，让角色加载该State即可应用动画
    """

    def __init__(
        self,
        imageset,
        image: pygame.Surface,
        state: State = State.create_idle(),
        direction=0,
        postapi=None,
    ):
        # direction:1左，0为右
        #
        # state记录当前动画的状态并改变动画
        self.image = image
        rect = image.get_rect()
        super().__init__(rect=rect, post_api=postapi)
        # 动画相关
        self.__imageset = imageset
        self.__current_state = state
        self.__direction = direction
        self.__current_anim = self.__imageset[self.__current_state.name]
        self.__frame = 0
        self.__frame_duration_count = 0
        self.__anim_loop_count = 0
        self.first_frame = False

    @property
    def faceing(self):
        return self.__direction

    @faceing.setter
    def faceing(self, x: int):
        self.__direction = x

    @property
    def state(self):
        return self.__current_state

    @state.setter
    def state(self, new_state):
        if self.__current_state.can_be_changed:
            self.__current_state = new_state
            self.__current_anim = self.__imageset[new_state.name]
        else:
            print("The current animation cant be interrputed")

    @property
    def current_frame(self):
        return self.__frame

    def change_state(self, new_state):
        if (
            self.__current_state.can_be_changed and self.state != new_state
        ) or new_state.high_priority:
            self.state = new_state
            self.__frame = 0
            self.__frame_duration_count = 0
            self.__anim_loop_count = 0

    @listening(c.StateEventCode.CHANGE_STATE)
    def change_state_by_event(self, event):
        if (
            self.__current_state.can_be_changed and self.state != event.body["state"]
        ) or event.body["state"].high_priority:
            self.state = event.body["state"]
            self.__frame = 0
            self.__frame_duration_count = 0
            self.__anim_loop_count = 0

    @listening(c.EventCode.ANIMSTEP)
    def anim_step(self, event):
        if (
            self.__frame_duration_count % self.state.duration == 0
            and self.__frame_duration_count != 0
        ):
            self.__frame_duration_count = 0
            self.__frame += 1
            self.first_frame = True
        if self.__frame % len(self.__current_anim[0]) == 0 and self.__frame != 0:
            self.__frame = 0
            self.__anim_loop_count += 1
        if self.__anim_loop_count == 1 and not self.state.is_loop:
            self.state.can_be_changed = True
            self.change_state(State.create_idle())
        if self.__anim_loop_count >= 999:
            self.__anim_loop_count = 0
        self.image = self.__current_anim[self.__direction][self.__frame]
        self.__frame_duration_count += 1


class Player(AnimatedSprite):
    """
    游戏角色类，包含对角色移动，动作，动画的控制
    """

    def __init__(self, post_api):
        if c.PLATFORM == "darwin":
            imageset = generate_imageset_for_mac("./assets/player/")
        else:
            imageset = generate_imageset("./assets/player/")
        image = imageset["idle"][0][0]
        super().__init__(image=image, imageset=imageset, postapi=post_api)
        self.rect.center = (500, 500)

    @listening(c.MoveEventCode.PREMOVE)
    def try_move(self, event):
        state = State.create_run()
        self.change_state(state)
        keys = pygame.key.get_pressed()
        move_offset = pygame.Vector2(0, 0)
        if self.state.info["can_move"]:
            if keys[pygame.K_a]:
                self.faceing = 1
                move_offset.x -= 5
            if keys[pygame.K_d]:
                self.faceing = 0
                move_offset.x += 5
            if keys[pygame.K_w]:
                move_offset.y -= 5
            if keys[pygame.K_s]:
                move_offset.y += 5
        self.post(
            EventLike(
                c.MoveEventCode.MOVEATTEMPT,
                sender=self.uuid,
                body={"move_offset": move_offset, "original_pos": self.rect.copy()},
            )
        )

    @listening(c.MoveEventCode.MOVEALLOW)
    def move(self, event):
        self.rect = event.body["pos"]
        self.post(EventLike(c.MoveEventCode.MOVECAMERA, body={"chara": self}))

    @listening(pygame.KEYDOWN)
    def behavior(self, event):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_j]:
            self.change_state(State.create_attack())
        elif keys[pygame.K_SPACE]:
            self.change_state(State.create_roll())

    @listening(c.EventCode.STEP)
    def step(self, event):
        if "frame_type" in self.state.info.keys():
            if self.state.info["frame_type"][self.current_frame] == 2:
                print("invincible")
            if (
                self.state.info["frame_type"][self.current_frame] == 1
                and self.first_frame
            ):
                self.first_frame = False
                print("attack")

    @listening(pygame.QUIT)
    def quit_game(self, event):
        Core.exit()


class Tile(EntityLike):
    def __init__(self, post_api, image, rect: pygame.Rect = None):
        rect: pygame.Rect = image.get_rect()
        super().__init__(post_api=post_api, rect=rect, image=image)

    @property
    def width(self):  # 获得tile的宽度
        return self.rect.width

    @property
    def height(self):  # 获得tile的长度
        return self.rect.height

    @property
    def tile_cord(self) -> tuple[int, int]:  # 可以把当前的贴图坐标计算出来
        return (self.rect.left // self.width, self.rect.top // self.height)

    @tile_cord.setter
    def tile_cord(
        self, new_cord: tuple[int, int]
    ):  # 可以通过贴图坐标直接自动设置rect的位置
        self.rect.left = new_cord[0] * self.width
        self.rect.top = new_cord[1] * self.height


class SceneLike(GroupLike):
    """
    场景类, 主要提供相机坐标, 图层控制, 以及进入与退出

    Attributes
    ----------
    core : Core
        核心
    camera_cord : Tuple[int, int]
        相机坐标 (绘制位置的负偏移量), 初始值为`(0, 0)`
    is_activated : bool
        场景是否被激活：调用`self.into`时设置为True, 调用`self.leave`时设置为False
    layers : collections.defaultdict[int, List[ListenerLike]]
        图层。键为整数, 代表绘制顺序 (从小到大)

    Methods
    -------
    into()
        进入场景
    leave()
        离开场景
    """

    # attributes
    __core: Core
    __camera_cord: Tuple[int, int]
    __map_size: Tuple[int, int]
    name: str
    is_activated: bool
    layers: collections.defaultdict[int, List[ListenerLike]]
    caches: Dict[str, Any]

    @property
    def core(self):
        """核心"""
        return self.__core

    @property
    def camera_cord(self) -> Tuple[int, int]:
        """
        相机坐标 (绘制位置的负偏移量)

        Notes
        ---
        初始值为`(0, 0)`
        """
        return self.__camera_cord

    @camera_cord.setter
    def camera_cord(
        self, new_cord: Tuple[int, int]
    ) -> None:  # 这个方法可以在设置相机的同时自动检测边缘
        x, y = new_cord
        if new_cord[0] < 0:
            x = 0
        elif new_cord[0] + self.core.window.get_width() > self.__map_size[0]:
            x = self.__map_size[0] - self.core.window.get_width()
        if new_cord[1] < 0:
            y = 0
        elif new_cord[1] + self.core.window.get_height() > self.__map_size[1]:
            y = self.__map_size[1] - self.core.window.get_height()
        result_cord = (x, y)
        self.__camera_cord = result_cord

    def __init__(
        self,
        core: Core,
        *,
        listen_receivers: Optional[Set[str]] = None,
        post_api: Optional[PostEventApiLike] = None,
        mapsize=(3000, 2000),
        name="",
        player=None,
    ):
        """
        Parameters
        ---
        core : Core
            核心
        post_api : (EventLike) -> None, optional, default = None
            发布事件函数, 一般使用`Core`的`add_event`
        listen_receivers : set[str], optional, default = {EVERYONE_RECEIVER, self.uuid}
            监听的接收者集合, 自动加上EVERYONE_RECEIVER与self.uuid
        """
        super().__init__(
            listen_receivers=listen_receivers,
            post_api=post_api if post_api is not None else core.add_event,
        )
        self.__core: Core = core
        self.__camera_cord: Tuple[int, int] = (0, 0)
        self.__map_size = mapsize
        self.layers: collections.defaultdict[int, List[ListenerLike]] = (
            collections.defaultdict(list)
        )
        self.caches: Dict[str, Any] = {}
        self.walls: list[EntityLike] = []
        self.is_activated = False
        self.name = name
        self.player = player
        self.enemies = []

    def update_camera_by_chara(self, chara: EntityLike):
        self.camera_cord = (
            chara.rect.centerx - self.core.window.get_width() / 2,
            chara.rect.centery - self.core.window.get_height() / 2,
        )

    def load_tilemap(
        self, config_file_path, scale=3
    ):  # tilemap的数据都是以json格式储存的
        self.layers[0] = []  # 图层的最低端都是地图
        with open(config_file_path, "r") as f:
            config = f.read()
        config = json.loads(config)  # 读取json并转换为python数据
        self.__map_size = (config[0]["width"] * scale, config[0]["height"] * scale)
        for tiles in config[1:]:
            image = pygame.image.load(f"./assets/mytiles/{tiles["name"]}")
            image = pygame.transform.scale(
                image, (image.get_width() * 3, image.get_height() * 3)
            )
            for cord in tiles["cord"]:
                tile = Tile(self.post_api, image)
                tile.tile_cord = cord
                if tiles["type"] == "wall":
                    self.walls.append(tile)
                self.add_listener(tile)
                self.layers[0].append(tile)

    def __enter__(self):
        """
        调用`self.into`, 提供给上下文管理器的接口
        """
        self.into()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        调用`self.leave`, 提供给上下文管理器的接口
        """
        self.leave()
        return False

    def into(self) -> None:
        """
        进入场景, `self.is_activated`设置为`True`
        """
        self.is_activated = True
        logger.info(f"Into {self.__class__}.")

    def leave(self) -> None:
        """
        离开场景, `self.is_activated`设置为`False`
        """
        self.is_activated = False
        logger.info(f"Leave {self.__class__}.")

    def listen(self, event: EventLike):
        """
        场景本体处理事件, 场景内成员 (`self.listeners`) 处理事件 (除了DRAW事件) 。

        Notes
        ---
        - DRAW事件会被场景捕获, 不会转发给成员。场景本身的`draw`方法根据`self.layers`顺序进行逐层绘制。
        """
        self.group_listen(event)
        if event.code == c.EventCode.DRAW:
            return
        self.member_listen(event)

    @listening(c.MoveEventCode.MOVECAMERA)
    def move_camera(self, event):
        self.update_camera_by_chara(event.body["chara"])

    @listening(c.MoveEventCode.MOVEATTEMPT)
    def judge_move(self, event):
        can_move_horizental = True  # 可垂直移动
        can_move_vertical = True  # 可水平移动
        new_rect = event.body["original_pos"].copy()
        rect_add_x_offset = event.body["original_pos"].move(
            (event.body["move_offset"].x, 0)
        )
        rect_add_y_offset = event.body["original_pos"].move(
            (0, event.body["move_offset"].y)
        )
        for wall in self.walls:
            if wall.rect.colliderect(rect_add_x_offset):
                can_move_horizental = False
                break
        for wall in self.walls:
            if wall.rect.colliderect(rect_add_y_offset):
                can_move_vertical = False
        if can_move_horizental:
            new_rect.x += event.body["move_offset"].x
        if can_move_vertical:
            new_rect.y += event.body["move_offset"].y
        self.post(
            EventLike(
                c.MoveEventCode.MOVEALLOW,
                body={"pos": new_rect},
            )
        )

    @listening(c.EventCode.DRAW)
    def draw(self, event: EventLike):
        """
        根据图层顺序, 在画布上绘制实体

        Listening
        ---
        DRAW : DrawEventBody
            window : pygame.Surface
                画布
            camera : tuple[int, int]
                镜头坐标（/负偏移量）

        Notes
        ---
        根据图层的键从小到大排序图层, 逐层处理。每个图层中的对象按照列表顺序接收DRAW事件。
        """
        window = self.core.window
        camera = self.camera_cord
        draw_event = EventLike.draw_event(window, camera=camera)

        layer_ids = sorted(self.layers.keys())
        for lid in layer_ids:
            layer = self.layers[lid]
            for listener in layer:
                listener.listen(draw_event)

    @listening(c.EventCode.KILL)
    def kill(self, event: EventLike):
        """
        根据`event.body["suicide"]`提供的UUID, 从场景中删除该成员

        Listening
        ---
        KILL : KillEventBody
            suicide : str
                即将被删除成员的UUID

        Notes
        ---
        需要被删除的成员会被`self.remove_listener`删除, 并从`self.layers`中被删除。
        """
        body: c.KillEventBody = event.body
        uuid = body["suicide"]
        for i in self.layers:
            self.layers[i][:] = [j for j in self.layers[i] if j.uuid != uuid]
        super().kill(event)


class SceneManager(ListenerLike):
    def __init__(self, post_api, scenelist, inital_scene_name):
        super().__init__(post_api=post_api)
        self.__scene_list = scenelist
        self.current_scene = self.__scene_list[inital_scene_name]

    def add_scene(self, scene: SceneLike):
        self.__scene_list[scene.name] = scene

    @listening(c.SceneEventCode.CHANGE_SCENE)
    def change_scene(self, event):
        if event.body["scene_name"] in self.__scene_list.keys():
            self.current_scene = self.__scene_list[event.body["scene_name"]]
            self.current_scene.player.rect.x = event.body["playerpos"][0]
            self.current_scene.player.rect.y = event.body["playerpos"][1]
        else:
            print("no such scene")

    @listening(c.SceneEventCode.RESTART)
    def restart_scene(self, event):
        self.__scene_list[event.body["scene_name"]] = event.body["pre_loaded_scene"]
