from itertools import count
from time import sleep
from tracemalloc import start
import pygame

import utils
import game_constants as c
from game_collections import EventLike, Core, listening, EntityLike, GroupLike
import os


def generate_imageset(path):
    imageset = {}
    for i in os.listdir(path):
        temp = [[], []]
        for j in os.listdir(os.path.join(path, i)):
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
            for j in os.listdir(os.path.join(path, i)):
                if j != ".DS_Store":
                    image = pygame.image.load(os.path.join(path, i, j))
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
        self, name: str, change_flag=True, loop_flag=True, info: dict = {}, duration=1
    ) -> None:
        self.name = name
        self.can_be_changed = change_flag
        self.is_loop = loop_flag
        self.duration = duration
        self.info = info

    @classmethod
    def create_idle(self):
        return self("idle", duration=15)

    @classmethod
    def create_run(self):
        return self("run", duration=5)

    @classmethod
    def create_attack(self):
        info = {"frame_type": [0, 0, 1, 0, 0, 0]}
        return self("attack", change_flag=False, loop_flag=False, duration=5, info=info)

    @classmethod
    def create_roll(self):
        info = {"frame_type": [0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0]}
        return self("roll", change_flag=False, loop_flag=False, duration=5, info=info)

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

    def change_state(self, new_state):
        if self.__current_state.can_be_changed and self.state != new_state:
            self.state = new_state
            self.__frame = 0
            self.__frame_duration_count = 0
            self.__anim_loop_count = 0

    @listening(c.StateEventCode.CHANGE_STATE)
    def change_state_by_event(self, event):
        if self.__current_state.can_be_changed and self.state != event.body["state"]:
            self.state = event.body["state"]
            self.__frame = 0
            self.__frame_duration_count = 0
            self.__anim_loop_count = 0

    @listening(c.EventCode.STEP)
    def step(self, event):
        if (
            self.__frame_duration_count % self.state.duration == 0
            and self.__frame_duration_count != 0
        ):
            self.__frame_duration_count = 0
            self.__frame += 1
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
