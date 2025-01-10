import collections
from json import load
from pydoc import plain
from random import randint, choice
import time
from turtle import listen, width

import math
import pygame
from loguru import logger

import os
from base.constants import EventCode
import game_constants as c
from base import (
    EventLike,
    ListenerLike,
    GroupLike,
    Core,
    PostEventApiLike,
    listening,
)
from game_collections import *
from utils import dist2

"""
该文件是基于game_collections中的基类更加具体的游戏内物体
包括Player，Enemy之类的
"""


class Player(AnimatedSprite):
    """
    游戏角色类，包含对角色移动，动作，动画的控制
    """

    def __init__(self, post_api):
        imageset = generate_imageset("./assets/player/")
        image = imageset["idle"][0][0]
        super().__init__(image=image, imageset=imageset, post_api=post_api)
        self.rect = pygame.Rect(0, 0, 63, 114)  # width 21*3 height 38*3
        self.rect.center = (500, 500)
        self.max_hp = 200
        self.hp = self.max_hp
        self.max_sp = 100
        self.sp = self.max_sp
        # sp消耗后不会马上回复，有冷却
        self.sp_recover_count_down_start = time.time()
        # 单位秒
        self.sp_recover_cooling_time = 1
        self.sp_recover_speed = 0.7
        self.damage = 100
        self.attack_range = [150, 114]
        self.in_dialog = False

    def _on_frame_begin(self):
        if self.state.name == "attack":
            if self.state.info["frame_type"][self.current_frame] == 1:
                # self.first_frame = False
                if self.faceing == 0:  # 设定攻击的范围
                    attack_rect = pygame.Rect(
                        self.rect.centerx,
                        self.rect.centery - self.rect.height // 2,
                        *self.attack_range,
                    )
                else:
                    attack_rect = pygame.Rect(
                        self.rect.centerx - self.attack_range[0],
                        self.rect.centery - self.rect.height // 2,
                        *self.attack_range,
                    )
                self.post(
                    EventLike(
                        c.BattleCode.PLAYERATTACK,
                        sender=self.uuid,
                        body={"rect": attack_rect, "damage": self.damage},
                    )
                )

    @listening(c.MoveEventCode.PREMOVE)
    def try_move(self, event):
        if not self.in_dialog:
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
        if not self.in_dialog:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_j] and self.sp > 0 and self.state.name in ("run", "idle"):
                self.sp -= 20
                self.sp_recover_count_down_start = time.time()
                self.change_state(State.create_attack())
            elif (
                keys[pygame.K_SPACE]
                and self.sp > 0
                and self.state.name in ("run", "idle")
            ):
                self.sp -= 10
                self.sp_recover_count_down_start = time.time()
                self.change_state(State.create_roll())
            # 回身斩
            elif (
                keys[pygame.K_k] and self.sp > 0 and self.state.name in ("run", "idle")
            ):
                self.sp -= 30
                self.sp_recover_count_down_start = time.time()
                self.faceing ^= 1
                self.change_state(State.create_attack())

    @listening(c.BattleCode.ENEMYATTACK)
    def take_damage(self, event):
        if self.rect.colliderect(event.body["attack_rect"]):
            if not (
                "frame_type" in self.state.info.keys()
                and self.state.info["frame_type"][self.current_frame] == 2
            ):
                self.hp -= event.body["damage"]
                self.change_state(State.create_hit())
                print(f"player_hp:{self.hp}")
            else:
                print("hit invincible")

    @listening(c.DialogEventCode.ACTIVATE_DIALOG)
    def a_d(self, event):
        self.in_dialog = True

    @listening(c.DialogEventCode.STOP_DIALOG)
    def s_d(self, event):
        self.in_dialog = False

    @listening(c.EventCode.STEP)
    def step(self, event):
        if (
            time.time() - self.sp_recover_count_down_start
            >= self.sp_recover_cooling_time
        ):
            if self.sp < self.max_sp:
                self.sp += self.sp_recover_speed
                if self.sp > self.max_sp:
                    self.sp = self.max_sp
        if self.sp < 0:
            self.sp = 0

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
        real_rect = rect.move(
            -(self.image.get_width() - rect.width) / 2,
            -(self.image.get_height() - rect.height) / 2,
        )
        if self.faceing == 0:
            attack_rect = pygame.Rect(
                self.rect.centerx,
                self.rect.centery - self.rect.height // 2,
                *self.attack_range,
            )
        else:
            attack_rect = pygame.Rect(
                self.rect.centerx - self.attack_range[0],
                self.rect.centery - self.rect.height // 2,
                *self.attack_range,
            )
        rect_max_hp_bar = pygame.rect.Rect(5, 5, self.max_hp * 2, 15)
        rect_hp_bar = pygame.rect.Rect(
            5, 5, self.max_hp * 2 * (self.hp / self.max_hp), 15
        )
        rect_max_sp_bar = pygame.rect.Rect(5, 25, self.max_sp * 1.5, 15)
        rect_sp_bar = pygame.rect.Rect(
            5, 25, self.max_sp * 1.5 * (self.sp / self.max_sp), 15
        )
        pygame.draw.rect(surface, (255, 0, 0), rect_max_hp_bar)
        pygame.draw.rect(surface, (0, 255, 0), rect_hp_bar)
        pygame.draw.rect(surface, (0, 0, 0), rect_max_sp_bar)
        pygame.draw.rect(surface, (255, 255, 0), rect_sp_bar)
        if self.image is not None:
            surface.blit(self.image, real_rect)
        if c.DEBUG and self.__class__.__name__ != "Tile":
            RED = (255, 0, 0)
            # rect
            pygame.draw.rect(surface, RED, rect, width=1)
            pygame.draw.rect(
                surface, "green", attack_rect.move(*(-i for i in offset)), width=1
            )
            pygame.draw.line(surface, RED, rect.topleft, offset, width=1)
            # font
            text_rect: pygame.Rect = rect.copy()
            text_rect.topleft = rect.bottomleft
            text_surface = utils.debug_text(f"{self.rect.topleft+self.rect.size}")
            surface.blit(text_surface, text_rect)


class Enemy(AnimatedSprite):
    def __init__(
        self,
        imageset=generate_imageset("./assets/skeleton/"),
        state: State = State.create_idle(),
        direction=0,
        post_api=None,
        target: EntityLike = None,
        max_hp=30,
        damage=10,
        money_drop=10,
    ):
        image = imageset["idle"][0][0]
        super().__init__(imageset, image, state, direction, post_api)
        self.target = target  # most case: Player
        self.max_hp = max_hp
        self.hp = max_hp
        self.damage = damage
        self.money_drop = money_drop
        self.found_target = False

    def _on_loop_end(self):
        if self.state.death_flag:
            self.post(EventLike(c.EventCode.KILL, body={"suicide": self.uuid}))

    @classmethod
    def create_self(cls, post_api):
        return cls(post_api=post_api)

    @listening(c.BattleCode.PLAYERATTACK)
    def take_damage(self, event):
        if self.rect.colliderect(event.body["rect"]):
            self.hp -= event.body["damage"]
            if self.hp <= 0:
                self.change_state(State.create_die())
                self.post(
                    EventLike(
                        c.ResourceCode.CHANGEMONEY, body={"money": self.money_drop}
                    )
                )
            else:
                self.change_state(State.create_hit())

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
        if self.faceing == 0:
            draw_rect = rect
        else:
            draw_rect = rect.move(
                -(self.image.get_width() - rect.width),
                -(self.image.get_height() - rect.height),
            )
        rect_red = rect.move(0, -10)
        rect_red.height = 10
        rect_light_green = rect.move(0, -10)
        green_width = (self.hp / self.max_hp) * self.rect.width
        rect_light_green.width = green_width
        rect_light_green.height = 5
        rect_dark_green = rect.move(0, -5)
        rect_dark_green.width = green_width
        rect_dark_green.height = 5
        pygame.draw.rect(surface, "red", rect_red)
        pygame.draw.rect(surface, (72, 219, 55), rect_dark_green)
        pygame.draw.rect(surface, (131, 245, 118), rect_light_green)
        if self.image is not None:
            surface.blit(self.image, draw_rect)
        if c.DEBUG and self.__class__.__name__ != "Tile":
            RED = (255, 0, 0)
            # rect
            pygame.draw.rect(surface, RED, rect, width=1)
            pygame.draw.rect(
                surface, "green", self.attack_rect.move(*(-i for i in offset)), width=1
            )
            pygame.draw.circle(
                surface,
                "blue",
                self.wander_dest + pygame.Vector2(*(-i for i in offset)),
                10,
            )
            pygame.draw.line(surface, RED, rect.topleft, offset, width=1)
            # font
            text_rect: pygame.Rect = rect.copy()
            text_rect.topleft = rect.bottomleft
            text_surface = utils.debug_text(f"{self.rect.topleft+self.rect.size}")
            surface.blit(text_surface, text_rect)


class Skeleton(Enemy):
    def __init__(
        self,
        imageset=generate_imageset("./assets/skeleton/"),
        state: State = State.create_idle(),
        direction=0,
        post_api=None,
        target: EntityLike = None,
        hp=30,
        damage=10,
        money_drop=10,
    ):
        super().__init__(
            imageset, state, direction, post_api, target, hp, damage, money_drop
        )
        self.attack_duration = 3  # second
        self.can_attack = True
        self.last_attack_time = time.time()
        self.attack_range = [24 * 3, 32 * 3]
        self.wander_dest = pygame.Vector2(self.rect.x, self.rect.y)
        self.wander_finished = True
        self.wander_range = (500, 1000)
        self.view2 = 100000  # 视野的平方

    @listening(c.CollisionEventCode.ENEMY_MOVE_ALLOW)
    def move_allow(self, event):
        self.rect = event.body["pos"]

    @listening(c.CollisionEventCode.ENEMY_MOVE_ATTEMPT_WANDER_ALLOW)
    def wander_allow(self, event):
        if event.body["can_move"]:
            self.rect = event.body["rect"]
        else:
            self.wander_finished = True

    @listening(c.EventCode.STEP)
    def step(self, event):
        # if self.hp <= 0:
        #     self.change_state(State.create_die())
        # reset attack flag
        if not self.can_attack:
            if time.time() - self.last_attack_time >= 3.0:
                self.can_attack = True
        # generate attack rect
        if self.faceing == 0:
            attack_rect = pygame.Rect(
                self.rect.centerx,
                self.rect.centery - self.rect.height // 2,
                *self.attack_range,
            )
        else:
            attack_rect = pygame.Rect(
                self.rect.centerx - self.attack_range[0],
                self.rect.centery - self.rect.height // 2,
                *self.attack_range,
            )
        self.attack_rect = attack_rect  # apply the new attack rect to self
        # do if found target
        if self.found_target:
            # judge if can attack
            if self.target.rect.colliderect(attack_rect):
                if self.can_attack:
                    self.change_state(State.create_skeletion_attack())
                    self.can_attack = False
                    self.last_attack_time = time.time()
            # if can move, move to player
            if self.state.info["can_move"]:
                self.change_state(State.create_run())
                angle_to_target = math.atan2(
                    self.target.rect.centery - self.rect.centery,
                    self.target.rect.centerx - self.rect.centerx,
                )
                # change direction according to velocity
                if math.cos(angle_to_target) >= 0:
                    self.faceing = 0
                else:
                    self.faceing = 1
                offset = pygame.Vector2(
                    5 * math.cos(angle_to_target),
                    5 * math.sin(angle_to_target),
                )
                # post the ENEMY_MOVE_ATTEMPT event
                self.post(
                    EventLike(
                        c.CollisionEventCode.ENEMY_MOVE_ATTEMPT,
                        sender=self.uuid,
                        body={
                            "move_offset": offset,
                            "original_pos": self.rect.copy(),
                            "velocity": 6,
                            "player_rect": self.target.rect,
                        },
                    )
                )
        # do if not found target
        else:
            # judge the distance between self and player
            if dist2(self.rect, self.target.rect) <= self.view2:
                # 10000 literally 100 pixels
                self.found_target = True
                print(self.found_target)
            # found player then set found player flag to true

            # if not find player
            else:
                # if finish a wander
                if self.wander_finished:
                    self.wander_finished = False
                    # set a new wander-to destination
                    self.wander_dest = pygame.Vector2(
                        self.rect.centerx
                        + choice(
                            (
                                randint(*(-i for i in self.wander_range[::-1])),
                                randint(*(i for i in self.wander_range)),
                            )
                        ),
                        self.rect.centery
                        + choice(
                            (
                                randint(*(-i for i in self.wander_range[::-1])),
                                randint(*(i for i in self.wander_range)),
                            )
                        ),
                    )
                # in wandering
                else:
                    # set run state
                    self.change_state(State.create_run())
                    # the angle to destination
                    angle_to_dest = math.atan2(
                        self.wander_dest.y - self.rect.centery,
                        self.wander_dest.x - self.rect.centerx,
                    )
                    if math.cos(angle_to_dest) >= 0:
                        self.faceing = 0
                    else:
                        self.faceing = 1
                    move_rect = self.rect.move(
                        3 * math.cos(angle_to_dest),
                        3 * math.sin(angle_to_dest),
                    )
                    # check if coillde with the destination point
                    if move_rect.collidepoint(self.wander_dest):
                        self.wander_finished = True
                    else:
                        self.post(
                            EventLike(
                                c.CollisionEventCode.ENEMY_MOVE_ATTEMPT_WANDER,
                                sender=self.uuid,
                                body={"rect": move_rect},
                            )
                        )

    def _on_frame_begin(self):
        if (
            "frame_type" in self.state.info.keys()
            and self.state.info["frame_type"][self.current_frame] == 1
        ):
            self.post(
                EventLike(
                    c.BattleCode.ENEMYATTACK,
                    body={"damage": self.damage, "attack_rect": self.attack_rect},
                )
            )


class FriendlyNpc(AnimatedSprite):
    def __init__(
        self, target: Player, imageset, image, state, direction, post_api=None
    ):
        super().__init__(imageset, image, state, direction, post_api)
        self.text_box = TextEntity(
            pygame.Rect(250, 550, 1, 1),
            font=TextEntity.get_zh_font(font_size=25),
            font_color=(0, 0, 0),
            dynamic_size=True,
        )
        self.target = target
        # 默认每一个npc都有一个welcome的对话作为初始对话
        self.dialog_activated = False
        self.current_dialog = "welcome"
        self.current_dialog_index = 0
        self.dialog_background = load_image_and_scale(
            "./assets/dialog_box/box1.png", pygame.Rect(0, 0, 1000, 300)
        )

    def listen(self, event: EventLike) -> None:
        super().listen(event)
        if self.dialog_activated:
            self.text_box.listen(event)

    @property
    def dialogs(self):
        return self.__dialogs

    def set_dialog(self, new_dia):
        self.__dialogs = new_dia

    @property
    def current_dialog(self):
        return self.__current_dialog

    @current_dialog.setter
    def current_dialog(self, new_tag):
        self.__current_dialog = new_tag
        self.current_dialog_index = 0

    @property
    def current_dialog_index(self):
        return self.__current_dialog_index

    @current_dialog_index.setter
    def current_dialog_index(self, new_index):
        max_len = len(self.dialogs[self.__current_dialog])
        self.__current_dialog_index = new_index % max_len
        self.text_box.set_text(
            self.dialogs[self.__current_dialog][self.__current_dialog_index][:-1]
        )

    def set_format_dialog(self, new_index, format_tuple):
        self.__current_dialog_index = new_index
        self.text_box.set_text(
            self.dialogs[self.__current_dialog][self.__current_dialog_index][:-1]
            % format_tuple
        )

    @listening(c.DialogEventCode.ACTIVATE_DIALOG)
    def activate_dialog(self, event):
        self.dialog_activated = True
        self.current_dialog = "welcome"

    @listening(c.DialogEventCode.STOP_DIALOG)
    def stop_dialog(self, event):
        self.dialog_activated = False

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
        if self.dialog_activated:
            surface.blit(
                self.dialog_background,
                (
                    surface.get_width() // 2 - self.dialog_background.get_width() // 2,
                    surface.get_height() - self.dialog_background.get_height(),
                ),
            )


class Tutor(FriendlyNpc):
    def __init__(self, target: Player, post_api=None):
        imageset = generate_imageset("./assets/friendly_npc/")
        image = imageset["idle"][0][0]
        state = State.create_idle()
        direction = 0
        self.set_dialog(
            {
                "welcome": [
                    "Hello$",
                    "我是你的指引者$",
                    "你需要通关这个地牢$",
                    "需要我帮你介绍这个游戏怎么玩吗? 1.介绍 2.谢谢，不用了@",
                ],
                "tutorial": [
                    "游戏的目标是通关这10层地牢，地牢难度会逐渐增大$",
                    "你有生命值，生命值降到0你就死了$",
                    "你还有体力，攻击和翻滚都会消耗体力，所以时刻注意你的体力$",
                    "每一层地牢需要你击败所有怪物才能进入下一层$",
                    "怪物会掉落金币，金币可以在中间出现的休息站中升级$",
                ],
                "farewell": ["祝你有愉快的一天$"],
            }
        )
        super().__init__(
            target,
            post_api=post_api,
            imageset=imageset,
            image=image,
            state=state,
            direction=direction,
        )

    @listening(c.EventCode.STEP)
    def step(self, event):
        if self.target.rect.x - self.rect.x >= 0:
            self.faceing = 0
        else:
            self.faceing = 1

    @listening(pygame.KEYDOWN)
    def on_keydown(self, event):
        # start==以下这一段是作为基础操作的，要用的时候复制
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE] and self.dialog_activated:
            self.post(
                EventLike(
                    c.DialogEventCode.STOP_DIALOG,
                    sender=self.uuid,
                    receivers={self.uuid, self.target.uuid},
                    body={},
                )
            )
            return
        if (
            (keys[pygame.K_e] or keys[pygame.K_SPACE])
            and self.dialog_activated
            and self.dialogs[self.current_dialog][self.current_dialog_index][-1] != "@"
        ):
            if self.current_dialog_index + 1 >= len(self.dialogs[self.current_dialog]):
                self.post(
                    EventLike(
                        c.DialogEventCode.STOP_DIALOG,
                        sender=self.uuid,
                        receivers={self.uuid, self.target.uuid},
                        body={},
                    )
                )
            else:
                self.current_dialog_index += 1
        # 按e交互
        if keys[pygame.K_e] and not self.dialog_activated:
            if dist2(self.rect, self.target.rect) <= 10000:
                self.post(
                    EventLike(
                        c.DialogEventCode.ACTIVATE_DIALOG,
                        sender=self.uuid,
                        receivers=set([self.uuid, self.target.uuid]),
                        body={},
                    )
                )
        # end==
        # 这里开始作为个性化内容
        if (
            self.dialog_activated
            and self.current_dialog == "welcome"
            and self.current_dialog_index == 3
        ):
            if keys[pygame.K_1]:
                self.current_dialog = "tutorial"
            elif keys[pygame.K_2]:
                self.current_dialog = "farewell"


class Bonfire(FriendlyNpc):
    def __init__(self, post_api, target: Player, resourcemanager: ResourceManager):
        imageset = generate_imageset("./assets/bonfire/", 1)
        image = imageset["idle"][0][0]
        state = State.create_idle()
        direction = 0
        self.set_dialog(
            {
                "welcome": [
                    "你好我是篝火$",
                    "有什么能帮你的$",
                    "1.继续冒险 2.升级 3.AI Feature@",
                ],
                "upgrade": [
                    "你想升级哪一项？1.血量(20金币) 2.体力(10金币) 3.攻击力(30金币)@"
                ],
                "upgrade1_success": ["升级成功，当前血量%d,升级后血量%d$"],
                "upgrade2_success": ["升级成功，当前体力%d,升级后体力%d$"],
                "upgrade3_success": ["升级成功，当前攻击%d,升级后攻击%d$"],
                "upgrade_fail": ["升级失败，金币不足$"],
            }
        )
        super().__init__(
            target=target,
            post_api=post_api,
            imageset=imageset,
            image=image,
            state=state,
            direction=direction,
        )
        self.resourcemanager = resourcemanager
        # self.change_state(State.create_idle())

    @listening(pygame.KEYDOWN)
    def on_keydown2(self, event):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE] and self.dialog_activated:
            self.post(
                EventLike(
                    c.DialogEventCode.STOP_DIALOG,
                    sender=self.uuid,
                    receivers={self.uuid, self.target.uuid},
                    body={},
                )
            )
            return
        if (
            (keys[pygame.K_e] or keys[pygame.K_SPACE])
            and self.dialog_activated
            and self.dialogs[self.current_dialog][self.current_dialog_index][-1] != "@"
        ):
            if self.current_dialog_index + 1 >= len(self.dialogs[self.current_dialog]):
                self.post(
                    EventLike(
                        c.DialogEventCode.STOP_DIALOG,
                        sender=self.uuid,
                        receivers={self.uuid, self.target.uuid},
                        body={},
                    )
                )
            else:
                self.current_dialog_index += 1
        # 按e交互
        if keys[pygame.K_e] and not self.dialog_activated:
            if dist2(self.rect, self.target.rect) <= 10000:
                self.post(
                    EventLike(
                        c.DialogEventCode.ACTIVATE_DIALOG,
                        sender=self.uuid,
                        receivers=set([self.uuid, self.target.uuid]),
                        body={},
                    )
                )
        if self.dialog_activated:
            if self.current_dialog == "welcome" and self.current_dialog_index == 2:
                if keys[pygame.K_1]:
                    self.post(EventLike(c.SceneEventCode.NEW_LEVEL))
                    self.post(
                        EventLike(
                            c.DialogEventCode.STOP_DIALOG,
                            sender=self.uuid,
                            receivers={self.uuid, self.target.uuid},
                            body={},
                        )
                    )
                    return
                elif keys[pygame.K_2]:
                    self.current_dialog = "upgrade"
            elif self.current_dialog == "upgrade" and self.current_dialog_index == 0:
                if keys[pygame.K_1]:
                    if self.resourcemanager.money < 20:
                        self.current_dialog = "upgrade_fail"
                    else:
                        self.current_dialog = "upgrade1_success"
                        self.set_format_dialog(
                            0, (self.target.max_hp, self.target.max_hp + 20)
                        )
                        self.target.max_hp += 20
                        self.target.hp += 20
                        self.resourcemanager.money -= 20
                elif keys[pygame.K_2]:
                    if self.resourcemanager.money < 10:
                        self.current_dialog = "upgrade_fail"
                    else:
                        self.current_dialog = "upgrade2_success"
                        self.set_format_dialog(
                            0, (self.target.max_sp, self.target.max_sp + 10)
                        )
                        self.target.max_sp += 10
                        self.resourcemanager.money -= 10
                elif keys[pygame.K_3]:
                    if self.resourcemanager.money < 30:
                        self.current_dialog = "upgrade_fail"
                    else:
                        self.current_dialog = "upgrade3_success"
                        self.set_format_dialog(
                            0, (self.target.damage, self.target.damage + 10)
                        )
                        self.target.damage += 10
                        self.resourcemanager.money -= 30
