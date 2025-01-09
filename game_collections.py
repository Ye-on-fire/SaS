from dis import pretty_flags
from hmac import new
import json
from pdb import post_mortem
import utils
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

from utils import *
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
        surface: pygame.Surface = body["window"]
        offset: Tuple[int, int] = body["camera"]

        rect = self.rect.move(*(-i for i in offset))
        if self.image is not None:
            surface.blit(self.image, rect)
        if c.DEBUG and self.__class__.__name__ != "Tile":
            RED = (255, 0, 0)
            # rect
            pygame.draw.rect(surface, RED, rect, width=1)
            pygame.draw.line(surface, RED, rect.topleft, offset, width=1)
            # font
            text_rect: pygame.Rect = rect.copy()
            text_rect.topleft = rect.bottomleft
            text_surface = utils.debug_text(f"{self.rect.topleft+self.rect.size}")
            surface.blit(text_surface, text_rect)


def generate_imageset(path):
    if c.PLATFORM.lower() == "mac":
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
    else:
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
        death_flag=False,
        prior_flag=False,
    ) -> None:
        self.name = name
        self.can_be_changed = change_flag
        self.is_loop = loop_flag
        self.duration = duration
        self.death_flag = death_flag
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
    def create_skeletion_attack(cls):
        info = {
            "frame_type": [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "can_move": False,
        }
        return cls("attack", change_flag=False, loop_flag=False, duration=3, info=info)

    @classmethod
    def create_roll(cls):
        info = {"frame_type": [0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0], "can_move": True}
        return cls("roll", change_flag=False, loop_flag=False, duration=3, info=info)

    @classmethod
    def create_die(cls):
        info = {"can_move": False}
        return cls(
            "die",
            change_flag=False,
            loop_flag=False,
            duration=3,
            death_flag=True,
            prior_flag=True,
            info=info,
        )

    @classmethod
    def create_hit(cls):
        info = {"can_move": False}
        return cls("hit", change_flag=False, duration=3, loop_flag=False, info=info)

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
        post_api=None,
    ):
        # direction:1左，0为右
        #
        # state记录当前动画的状态并改变动画
        self.image = image
        rect = image.get_rect()
        super().__init__(rect=rect, post_api=post_api)
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
        self.__current_state = new_state
        self.__current_anim = self.__imageset[new_state.name]

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

    def _on_frame_begin(self):
        """
        用来在子类中增加在每一动画帧开始时要做的事件
        """
        pass

    def _on_loop_end(self):
        """
        用来在不循环的动画结束时做的事情
        """
        pass

    @listening(c.EventCode.ANIMSTEP)
    def anim_step(self, event):
        if (
            self.__frame_duration_count % self.state.duration == 0
            and self.__frame_duration_count != 0
        ):
            self._on_frame_begin()
            self.__frame_duration_count = 0
            self.__frame += 1
            # self.first_frame = True
        if self.__frame % len(self.__current_anim[0]) == 0 and self.__frame != 0:
            self.__frame = 0
            self.__anim_loop_count += 1
        if self.__anim_loop_count == 1 and not self.state.is_loop:
            self.state.can_be_changed = True
            self._on_loop_end()
            self.change_state(State.create_idle())
        if self.__anim_loop_count >= 999:
            self.__anim_loop_count = 0
        self.image = self.__current_anim[self.__direction][self.__frame]
        self.__frame_duration_count += 1


class Tile(EntityLike):
    def __init__(
        self,
        post_api,
        image,
        rect: pygame.Rect = None,
        map_tile_width=16,
        map_tile_height=16,
    ):
        rect: pygame.Rect = image.get_rect()
        super().__init__(post_api=post_api, rect=rect, image=image)
        self.map_tile_width = map_tile_width
        self.map_tile_height = map_tile_height

    @property
    def width(self):  # 获得tile的宽度
        return self.rect.width

    @property
    def height(self):  # 获得tile的长度
        return self.rect.height

    @property
    def tile_width(self):
        return self.rect.width // self.map_tile_width

    @property
    def tile_height(self):
        return self.rect.height // self.map_tile_height

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

    @property
    def map_width(self):
        return self.__map_size[0]

    @property
    def map_height(self):
        return self.__map_size[1]

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
        self.__player = player
        self.update_camera_by_chara(self.__player)
        self.enemies = []

    @property
    def player(self):
        return self.__player

    @player.setter
    def player(self, new_player):
        self.__player = new_player
        self.update_camera_by_chara(new_player)

    def update_camera_by_chara(self, chara: EntityLike):
        self.camera_cord = (
            chara.rect.centerx - self.core.window.get_width() / 2,
            chara.rect.centery - self.core.window.get_height() / 2,
        )

    def add_listener(self, listener: ListenerLike, layer_id, solid=False) -> None:
        """
        Scenelike的添加组员方法，还能向图层中添加id
        """
        super().add_listener(listener)
        self.layers[layer_id].append(listener)
        if solid:
            self.walls.append(listener)

    def load_tilemap(
        self, config_file_path, scale=3
    ):  # tilemap的数据都是以json格式储存的
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
                    self.add_listener(tile, 0, True)
                else:
                    self.add_listener(tile, 0)
        print("load map complete")

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
                break
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

    @listening(c.CollisionEventCode.ENEMY_MOVE_ATTEMPT)
    def judge_enemy_move(self, event):
        if (
            event.body["original_pos"]
            .move(event.body["move_offset"])
            .colliderect(event.body["player_rect"])
        ):
            return
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
                break
        if can_move_horizental:
            new_rect.x += event.body["move_offset"].x
        else:
            new_rect.x += event.body["velocity"] * -sign(event.body["move_offset"].x)
        if can_move_vertical:
            new_rect.y += event.body["move_offset"].y
        else:
            new_rect.y += event.body["velocity"] * -sign(event.body["move_offset"].y)
        self.post(
            EventLike(
                c.CollisionEventCode.ENEMY_MOVE_ALLOW,
                receivers=set([event.sender]),
                body={"pos": new_rect},
            )
        )

    @listening(c.CollisionEventCode.ENEMY_MOVE_ATTEMPT_WANDER)
    def judge_wander(self, event):
        for wall in self.walls:
            if wall.rect.colliderect(event.body["rect"]):
                self.post(
                    EventLike(
                        c.CollisionEventCode.ENEMY_MOVE_ATTEMPT_WANDER_ALLOW,
                        receivers=set([event.sender]),
                        body={"can_move": False},
                    )
                )
                return
        self.post(
            EventLike(
                c.CollisionEventCode.ENEMY_MOVE_ATTEMPT_WANDER_ALLOW,
                receivers=set([event.sender]),
                body={"can_move": True, "rect": event.body["rect"]},
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

    @listening(pygame.QUIT)
    def quit_game(self, event):
        Core.exit()


class TextEntity(EntityLike):
    """
    文字框 (左上对齐)

    Methods
    ---
    set_text(self, text: str = "") -> None
        设置文本框文本
    get_zh_font(font_size: int, *, bold=False, italic=False) -> pygame.font.Font
        获取支持中文的字体, 如果系统中没有找到支持的字体, 则返回pygame默认字体。

    Attributes
    ---
    font : pygame.font.Font
        字体 (含字号)
    font_color : ColorValue
        字体颜色
    back_ground : ColorValue
        背景颜色
    """

    # Attributes
    font: pygame.font.Font
    font_color: c.ColorValue
    back_ground: c.ColorValue

    @staticmethod
    def get_zh_font(font_size: int, *, bold=False, italic=False) -> pygame.font.Font:
        """
        获取支持中文的字体, 如果系统中没有找到支持的字体, 则返回pygame默认字体。

        Parameters
        ---
        font_size : int
            字号
        bold : bool, default = False
            加粗 (仅当在系统中找到支持中文字体时生效)
        italic : bool, default = False
            斜体 (仅当在系统中找到支持中文字体时生效)

        Notes
        ---
        中文字体查找顺序
        SimHei, microsoftyahei, notosanscjk
        """
        available_fonts = pygame.font.get_fonts()
        font_name = None
        for i in ["microsoftyahei", "SimHei", "notosanscjk"]:
            if i not in available_fonts:
                continue
            font_name = i
            break

        if font_name is None:
            return pygame.font.Font(None, font_size)
        return pygame.font.SysFont(font_name, font_size, bold, italic)

    def __init__(
        self,
        rect: pygame.Rect,
        *,
        font: pygame.font.Font = None,
        font_color: c.ColorValue = (255, 255, 255),
        back_ground: c.ColorValue = (0, 0, 0, 0),
        text: str = "",
        dynamic_size: bool = False,
    ):
        """
        Parameters
        ---
        rect : pygame.Rect
            文本框
        font : pygame.font.Font, default = None
            字体
        font_color : ColorValue, default  = (255, 255, 255)
            字体颜色
        back_ground : ColorValue, default  = (0, 0, 0, 0)
            背景颜色
        text : str = ""
            文字
        dynamic_size : bool, default = False
            是否在设置文字时, 自动重新更新文本框大小
        """
        super().__init__(rect)
        self.font: pygame.font.Font = font if font is not None else self.get_zh_font()
        self.font_color: c.ColorValue = font_color
        self.back_ground: c.ColorValue = back_ground
        self.dynamic_size: bool = dynamic_size
        self.set_text(text)

    def set_text(self, text: str = "") -> None:
        """
        设置文本框文本

        Notes
        ---
        当`self.dynamic_size`为True时, 会自动更新文本框大小
        """
        # ===几何计算
        line_width_list: list[int] = []
        line_offset_list: list[int] = []
        current_offset: int = 0
        for line in text.splitlines():
            line_offset_list.append(current_offset)
            line_width, line_height = self.font.size(line)
            current_offset += line_height
            line_width_list.append(line_width)
        max_width = max(line_width_list) if line_width_list else 0
        # ===resize
        if self.dynamic_size:
            self.rect.size = (max_width, current_offset)
        # ===文本框背景
        text_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        text_surface.fill(self.back_ground)
        # ===绘制文本
        for line, offset in zip(text.splitlines(), line_offset_list):
            text_surface.blit(
                self.font.render(line, True, self.font_color), (0, offset)
            )
        self.image = text_surface

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
        surface: pygame.Surface = body["window"]
        offset: Tuple[int, int] = body["camera"]

        if self.image is not None:
            surface.blit(self.image, self.rect)
        # if c.DEBUG and self.__class__.__name__ != "Tile":
        #     RED = (255, 0, 0)
        #     # rect
        #     pygame.draw.rect(surface, RED, rect, width=1)
        #     pygame.draw.line(surface, RED, rect.topleft, offset, width=1)
        #     # font
        #     text_rect: pygame.Rect = rect.copy()
        #     text_rect.topleft = rect.bottomleft
        #     text_surface = utils.debug_text(f"{self.rect.topleft+self.rect.size}")
        #     surface.blit(text_surface, text_rect)
        #


class SceneManager(ListenerLike):
    # 用来管理场景和切换场景
    def __init__(self, post_api, scenelist, inital_scene_name):
        super().__init__(post_api=post_api)
        self.__scene_list = scenelist
        self.current_scene = self.__scene_list[inital_scene_name]

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


class ResourceManager(ListenerLike):
    # 用来管理全局属性
    def __init__(self, post_api):
        super().__init__(post_api=post_api)
        self.money = 0
        self.difficulty = 1

    @listening(c.ResourceCode.CHANGEMONEY)
    def change_money(self, event):
        self.money += event.body["money"]
        print("current_money:%d" % self.money)
