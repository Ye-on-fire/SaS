from itertools import count
from time import sleep
from tracemalloc import start
import pygame

import utils
import game_constants as c
from game_collections import EventLike, Core, listening, EntityLike, GroupLike


class State:
    def __init__(
        self, name: str, change_flag=True, loop_flag=True, info: dict = {}
    ) -> None:
        self.name = name
        self.can_be_changed = change_flag
        self.is_loop = loop_flag
        self.info = info


class AnimatedSprite(EntityLike):
    def __init__(
        self,
        imageset: Dict,
        image: pygame.Surface,
        state: State = State("idle"),
        direction=0,
    ):
        # direction:1左，0为右
        #
        # state记录当前动画的状态并改变动画
        super().__init__(self)
        self.image = image
        self.rect = image.get_rect()
        # 动画相关
        self.__imageset = imageset
        self.__current_state = state
        self.__direction = direction
        self.__current_anim = self.__imageset[self.__current_state.name][
            self.__direction
        ]
        self.__frame = -1
        self.__anim_loop_count = -1

    @property
    def state(self):
        return self.__current_state

    @state.setter
    def set_state(self, new_state):
        if self.__current_state.can_be_changed:
            self.__current_state = new_state
            self.__current_anim = self.__imageset[new_state.name][self.__direction]
        else:
            print("The current animation cant be interrputed")

    @listening(c.StateEventCode.CHANGE_STATE)
    def change_state(self, new_state):
        if self.__current_state.can_be_changed:
            self.state = new_state
            self.__frame = -1
            self.__anim_loop_count = -1

    @listening(c.EventCode.STEP)
    def step(self):
        self.__frame += 1
        if self.__frame % len(self.current_anim) == 0:
            self.__anim_loop_count += 1
            self.__frame = 0
        if not self.state.is_loop:
            event = EventLike(
                c.StateEventCode.CHANGE_STATE, body={"state": State("idle")}
            )
            self.post(event)
        self.image = self.__current_anim[self.__frame]
