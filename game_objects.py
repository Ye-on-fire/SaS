import collections
from openai import OpenAI
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

    def __init__(self, post_api, resourcemanager):
        imageset = generate_imageset("./assets/player/")
        image = imageset["idle"][0][0]
        super().__init__(image=image, imageset=imageset, post_api=post_api)
        self.rect = pygame.Rect(0, 0, 63, 114)  # width 21*3 height 38*3
        self.rect.center = (500, 500)
        self.max_hp = 100
        self.hp = self.max_hp
        self.max_sp = 70
        self.sp = self.max_sp
        # sp消耗后不会马上回复，有冷却
        self.sp_recover_count_down_start = time.time()
        # 单位秒
        self.sp_recover_cooling_time = 1
        self.sp_recover_speed = 0.7
        self.damage = 20
        self.attack_range = [150, 114]
        self.in_dialog = False
        self.moneyicon = load_image_and_scale(
            "./assets/mytiles/soul.png", pygame.Rect(0, 0, 48, 48)
        )
        self.moneytextbox = TextEntity(
            pygame.Rect(60, 650, 1, 1),
            font=pygame.font.Font("./assets/fonts/FangSim.ttf", 48),
            font_color=(255, 255, 0),
            dynamic_size=True,
        )
        self.resourcemanager = resourcemanager

    def _on_frame_begin(self):
        if self.state.name == "attack":
            print("player attackframe: %d" % self.current_frame)
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

    def listen(self, event: EventLike) -> None:
        super().listen(event)
        self.moneytextbox.listen(event)

    def _on_loop_end(self):
        if self.state.name == "die":
            Core.play_music("./assets/bgm/die.ogg", loop=1)
            self.post(
                EventLike(
                    c.SceneEventCode.CHANGE_SCENE, body={"scene_name": "gameover"}
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
        if self.hp <= 0:
            self.change_state(State.create_die())

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
        self.moneytextbox.set_text(str(self.resourcemanager.money))

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
        pygame.draw.rect(surface, (255, 0, 0), rect_max_hp_bar, border_radius=10)
        pygame.draw.rect(surface, (0, 255, 0), rect_hp_bar, border_radius=10)
        pygame.draw.rect(surface, (0, 0, 0), rect_max_sp_bar, border_radius=10)
        pygame.draw.rect(surface, (255, 255, 0), rect_sp_bar, border_radius=10)
        pygame.draw.rect(
            surface, (52, 67, 235), rect_max_hp_bar, width=1, border_radius=10
        )
        pygame.draw.rect(
            surface, (52, 67, 235), rect_max_sp_bar, width=1, border_radius=10
        )
        surface.blit(self.moneyicon, (10, 650))
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
    def create_self(cls, post_api, hp, damage, money_drop):
        return cls(post_api=post_api, hp=hp, damage=damage, money_drop=money_drop)

    @listening(c.BattleCode.PLAYERATTACK)
    def take_damage(self, event):
        if not self.state.death_flag:
            if self.rect.colliderect(event.body["rect"]):
                self.hp -= event.body["damage"]
                if self.hp <= 0:
                    self.hp = 0
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
        rect_light_green.height = 10
        pygame.draw.rect(surface, "red", rect_red, border_radius=5)
        pygame.draw.rect(surface, (131, 245, 118), rect_light_green, border_radius=5)
        if self.image is not None:
            surface.blit(self.image, draw_rect)
        if c.DEBUG and self.__class__.__name__ != "Tile":
            RED = (255, 0, 0)
            # rect
            pygame.draw.rect(surface, RED, rect, width=1)
            # pygame.draw.rect(
            #     surface, "green", self.attack_rect.move(*(-i for i in offset)), width=1
            # )
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
        if self.state.name == "attack":
            print(self.current_frame)
            if self.state.info["frame_type"][self.current_frame] == 1:
                self.post(
                    EventLike(
                        c.BattleCode.ENEMYATTACK,
                        body={"damage": self.damage, "attack_rect": self.attack_rect},
                    )
                )


class Projectile(AnimatedSprite):
    def __init__(self, start_pos, end_pos, vel, post_api=None):
        imageset = generate_imageset("./assets/projectile/")
        image = imageset["idle"][0][0]
        super().__init__(imageset, image, State.create_idle(), 0, post_api)
        angle = math.atan2(end_pos[1] - start_pos[1], end_pos[0] - start_pos[0])
        self.damage = 30

        self.velx = vel * math.cos(angle)
        self.vely = vel * math.sin(angle)

    @listening(c.EventCode.STEP)
    def step(self, event):
        self.post(
            EventLike(
                c.CollisionEventCode.PROJECTILE_MOVE_ATTEMPT,
                sender=self.uuid,
                body={
                    "rect": self.rect.move(self.velx, self.vely),
                    "damage": self.damage,
                },
            )
        )

    @listening(c.CollisionEventCode.PROJECTILE_MOVE_ALLOW)
    def move_allow(self, event):
        self.rect = event.body["rect"]


class Boss(Enemy):
    def __init__(
        self,
        imageset=generate_imageset("./assets/boss/", 2),
        state: State = State.create_idle(),
        direction=0,
        post_api=None,
        target: EntityLike = None,
        hp=1000,
        damage=10,
        money_drop=10,
    ):
        super().__init__(
            imageset, state, direction, post_api, target, hp, damage, money_drop
        )
        self.rect = pygame.Rect(720, 400, 56 * 2, 100 * 2)
        self.attack_duration = 3
        self.last_attack_time = time.time() - self.attack_duration + 2
        self.summoned = False

    def _on_loop_end(self):
        if self.state.name == "die":
            Core.play_music("./assets/bgm/victory.ogg", 1)
            self.post(
                EventLike(c.SceneEventCode.CHANGE_SCENE, body={"scene_name": "victory"})
            )

    def attack1(self):
        self.faceing = 0
        self.rect.centerx = 100
        self.rect.centery = 480
        self.change_state(State.create_attack())
        amount = 8
        for i in range(amount):
            prj = Projectile(
                (120, 48 + 864 / (amount + 1) * i),
                (121, 48 + 864 / (amount + 1) * i),
                10,
                self.post_api,
            )
            prj.rect.centerx = 120
            prj.rect.centery = 48 + 864 / (amount + 1) * i
            self.post(EventLike(c.SceneEventCode.ADD_LISTENER, body={"listener": prj}))

    def attack2(self):
        self.faceing = 1
        self.rect.centerx = 1340
        self.rect.centery = 480
        self.change_state(State.create_attack())
        amount = 8
        for i in range(amount):
            prj = Projectile(
                (1320, 48 + 864 / (amount + 1) * i),
                (1319, 48 + 864 / (amount + 1) * i),
                10,
                self.post_api,
            )
            prj.rect.centerx = 1320
            prj.rect.centery = 48 + 864 / (amount + 1) * i
            self.post(EventLike(c.SceneEventCode.ADD_LISTENER, body={"listener": prj}))

    def attack3(self):
        self.faceing = 0
        self.rect.centerx = 720
        self.rect.centery = 90
        self.change_state(State.create_attack())
        amount = 10
        for i in range(amount):
            prj = Projectile(
                (48 + i * 1392 / (amount + 1), 100),
                (48 + i * 1392 / (amount + 1), 101),
                10,
                self.post_api,
            )
            prj.rect.centerx = 48 + i * 1392 / (amount + 1)
            prj.rect.centery = 100
            self.post(EventLike(c.SceneEventCode.ADD_LISTENER, body={"listener": prj}))

    def attack4(self):
        self.faceing = 1
        self.rect.centerx = 720
        self.rect.centery = 830
        self.change_state(State.create_attack())
        amount = 10
        for i in range(amount):
            prj = Projectile(
                (48 + i * 1392 / (amount + 1), 830),
                (48 + i * 1392 / (amount + 1), 829),
                10,
                self.post_api,
            )
            prj.rect.centerx = 48 + i * 1392 / (amount + 1)
            prj.rect.centery = 830
            self.post(EventLike(c.SceneEventCode.ADD_LISTENER, body={"listener": prj}))

    def attack5(self):
        if self.rect.x - self.target.rect.x:
            self.faceing = 1
        else:
            self.faceing = 0
        self.rect.centerx = randint(400, 1000)
        self.rect.centery = randint(300, 650)
        self.change_state(State.create_attack())
        amount = 4
        offset = 300
        for i in range(amount):
            x = choice(
                (
                    randint(
                        self.target.rect.left - offset, self.target.rect.left - 150
                    ),
                    randint(
                        self.target.rect.right + 150, self.target.rect.right + offset
                    ),
                )
            )
            y = choice(
                (
                    randint(self.target.rect.top - offset, self.target.rect.top - 150),
                    randint(
                        self.target.rect.bottom + 150, self.target.rect.bottom + offset
                    ),
                )
            )
            prj = Projectile(
                (x, y),
                (self.target.rect.centerx, self.target.rect.centery),
                6,
                self.post_api,
            )
            prj.rect.centerx = x
            prj.rect.centery = y
            self.post(EventLike(c.SceneEventCode.ADD_LISTENER, body={"listener": prj}))

    def summon(self):
        self.change_state(State.create_attack())
        for i in range(2):
            skeleton = Skeleton(
                post_api=self.post_api,
                target=self.target,
                hp=100,
                damage=20,
                money_drop=0,
            )
            skeleton.rect.x = choice((150, 1000))
            skeleton.rect.y = choice((150, 800))
            skeleton.found_target = True
            self.post(
                EventLike(c.SceneEventCode.ADD_LISTENER, body={"listener": skeleton})
            )

    @listening(c.BattleCode.SET_LAST_ATTACK)
    def set_last_attack(self, event):
        self.last_attack_time = time.time() - self.attack_duration + 2

    @listening(c.EventCode.STEP)
    def step(self, event):
        if self.hp <= self.max_hp // 2 and not self.summoned:
            self.summon()
            self.summoned = True
        if time.time() - self.last_attack_time >= self.attack_duration:
            if self.target.rect.left > 1152:
                self.attack1()
            elif self.target.rect.right < 288:
                self.attack2()
            elif (
                self.target.rect.top < 192
                and self.target.rect.left >= 288
                and self.target.rect.right <= 1152
            ):
                self.attack4()
            elif (
                self.target.rect.bottom > 768
                and self.target.rect.left >= 288
                and self.target.rect.right <= 1152
            ):
                self.attack3()
            else:
                self.attack5()
            self.last_attack_time = time.time()

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
        rect_max_hp_bar = pygame.rect.Rect(220, 55, 800, 20)
        rect_hp_bar = pygame.rect.Rect(220, 55, 800 * (self.hp / self.max_hp), 20)
        pygame.draw.rect(surface, (255, 0, 0), rect_max_hp_bar)
        pygame.draw.rect(surface, (0, 255, 0), rect_hp_bar)
        pygame.draw.rect(surface, (255, 255, 255), rect_max_hp_bar, width=2)
        if self.image is not None:
            surface.blit(self.image, real_rect)
        if c.DEBUG and self.__class__.__name__ != "Tile":
            RED = (255, 0, 0)
            # rect
            pygame.draw.rect(surface, RED, rect, width=1)
            # font
            text_rect: pygame.Rect = rect.copy()
            text_rect.topleft = rect.bottomleft
            text_surface = utils.debug_text(f"{self.rect.topleft+self.rect.size}")
            surface.blit(text_surface, text_rect)


class FriendlyNpc(AnimatedSprite):
    def __init__(
        self, target: Player, imageset, image, state, direction, post_api=None
    ):
        super().__init__(imageset, image, state, direction, post_api)
        self.text_box = TextEntity(
            pygame.Rect(250, 550, 1, 1),
            font=pygame.font.Font("./assets/fonts/FangSim.ttf", 25),
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
                    "这个地牢里有一个死灵法师$",
                    "他一直在创造骷髅$",
                    "给人们的生活带来了困扰$",
                    "你的目标是打败他$",
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
            and self.current_dialog_index == 6
        ):
            if keys[pygame.K_1]:
                self.current_dialog = "tutorial"
            elif keys[pygame.K_2]:
                self.current_dialog = "farewell"


class Bonfire(FriendlyNpc):
    def __init__(self, post_api, target: Player, resourcemanager: ResourceManager):
        imageset = generate_imageset("./assets/bonfire/", 1)
        image = imageset["idle"][0][0]
        state = State("idle", duration=5)
        direction = 0
        self.set_dialog(
            {
                "welcome": [
                    "你好我是篝火$",
                    "有什么能帮你的$",
                    "1.继续冒险 2.升级@",
                ],
                "upgrade": [
                    "你想升级哪一项？1.血量(%d金币) 2.体力(%d金币) 3.攻击力(%d金币)@"
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
        self.hp_money = 20
        self.sp_money = 15
        self.attack_money = 25
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
                    self.post(
                        EventLike(
                            c.DialogEventCode.STOP_DIALOG,
                            sender=self.uuid,
                            receivers={self.uuid, self.target.uuid},
                            body={},
                        )
                    )
                    Core.play_music("./assets/bgm/battleground.mp3")
                    self.post(EventLike(c.SceneEventCode.NEW_LEVEL))
                    return
                elif keys[pygame.K_2]:
                    self.current_dialog = "upgrade"
                    self.set_format_dialog(
                        0, (self.hp_money, self.sp_money, self.attack_money)
                    )
                # 作弊功能
                elif keys[pygame.K_3]:
                    self.target.max_hp = 100000
                    self.target.hp = 100000
                    self.target.max_sp = 100000
                    self.target.sp = 100000
                elif keys[pygame.K_4]:
                    self.target.damage = 100000
                elif keys[pygame.K_5]:
                    self.resourcemanager.money = 100000
            elif self.current_dialog == "upgrade" and self.current_dialog_index == 0:
                if keys[pygame.K_1]:
                    if self.resourcemanager.money < self.hp_money:
                        self.current_dialog = "upgrade_fail"
                    else:
                        self.current_dialog = "upgrade1_success"
                        self.set_format_dialog(
                            0, (self.target.max_hp, self.target.max_hp + 20)
                        )
                        self.target.max_hp += 20
                        self.target.hp += 20
                        self.resourcemanager.money -= self.hp_money
                        self.hp_money += 25
                elif keys[pygame.K_2]:
                    if self.resourcemanager.money < self.sp_money:
                        self.current_dialog = "upgrade_fail"
                    else:
                        self.current_dialog = "upgrade2_success"
                        self.set_format_dialog(
                            0, (self.target.max_sp, self.target.max_sp + 10)
                        )
                        self.target.max_sp += 10
                        self.resourcemanager.money -= self.sp_money
                        self.sp_money += 30
                elif keys[pygame.K_3]:
                    if self.resourcemanager.money < self.attack_money:
                        self.current_dialog = "upgrade_fail"
                    else:
                        self.current_dialog = "upgrade3_success"
                        self.set_format_dialog(
                            0, (self.target.damage, self.target.damage + 10)
                        )
                        self.target.damage += 8
                        self.resourcemanager.money -= self.attack_money
                        self.attack_money += 35


class Healer(AnimatedSprite):
    def __init__(self, target: Player, post_api=None):
        imageset = generate_imageset("./assets/healer/", 1)
        image = imageset["idle"][0][0]
        super().__init__(imageset, image, post_api=post_api, direction=1)
        self.target = target
        self.dialog_background = load_image_and_scale(
            "./assets/dialog_box/box1.png", pygame.Rect(0, 0, 1000, 300)
        )
        self.prompt_box = TextEntity(
            pygame.Rect(200, 550, 1, 1),
            font=pygame.font.Font("./assets/fonts/FangSim.ttf", 25),
            font_color=(0, 0, 0),
            dynamic_size=True,
        )
        self.input_box = TextEntity(
            pygame.Rect(200, 650, 1, 1),
            font=pygame.font.Font("./assets/fonts/FangSim.ttf", 25),
            font_color=(0, 0, 0),
            dynamic_size=True,
        )
        self.input_text = ""

        self.dialog_activated = False
        self.client = OpenAI(
            base_url="http://10.15.88.73:5031/v1",
            api_key="ollama",  # required but ignored
        )
        self.messages: List[Dict] = [
            {
                "role": "system",
                "content": """You are now a healer in a rpg game. 
                            The player will require you to heal him. 
                            When he needs a heal, he's request must contain word "need" and "heal".In this case,your anwser must be "$heal$" without any other words.
                            When his request doesn't contain "need" or "heal", normally reply to him in less than 15 words. The content can be blaming him for his carelessness to lose so much hp""",
            }
        ]

    @listening(c.DialogEventCode.ACTIVATE_DIALOG)
    def activate_dialog(self, event):
        self.dialog_activated = True
        self.prompt_box.set_text("I'm your healer.How can I help you?")

    @listening(c.DialogEventCode.STOP_DIALOG)
    def stop_dialog(self, event):
        self.dialog_activated = False

    @listening(pygame.KEYDOWN)
    def on_keydown(self, event):
        keys = pygame.key.get_pressed()
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
            if keys[pygame.K_RETURN]:
                self.messages.append({"role": "user", "content": self.input_text})
                self.input_text = ""
                response = self.client.chat.completions.create(
                    model="llama3.2",
                    messages=self.messages,  # a list of dictionary contains all chat dictionary
                )
                # 提取模型回复
                assistant_reply = response.choices[0].message.content
                if "$heal$" in assistant_reply:
                    self.target.hp = self.target.max_hp
                    assistant_reply = assistant_reply.replace(
                        "$heal$", "You are healed"
                    )
                self.prompt_box.set_text(assistant_reply)
                self.messages.append({"role": "assistant", "content": assistant_reply})
            elif keys[pygame.K_ESCAPE]:
                self.messages: List[Dict] = [
                    {
                        "role": "system",
                        "content": """You are now a healer in a rpg game. 
                                    The player will require you to heal him. 
                                    When he needs a heal, he's request must contain word "need" and "heal".In this case,your anwser must be "$heal$" without any other words.
                                    When his request doesn't contain "need" or "heal", normally reply to him in less than 15 words. The content can be blaming him for his carelessness to lose so much hp""",
                    }
                ]
                self.post(
                    EventLike(
                        c.DialogEventCode.STOP_DIALOG,
                        sender=self.uuid,
                        receivers={self.uuid, self.target.uuid},
                        body={},
                    )
                )
            elif keys[pygame.K_BACKSPACE]:
                self.input_text = self.input_text[:-1]
                # self.input_box.set_text(self.input_text)
            else:
                self.input_text += event.unicode
                # self.input_box.set_text(self.input_text)

    @listening(c.EventCode.STEP)
    def step(self, event):
        self.input_box.set_text(">" + self.input_text + "|")

    def listen(self, event: EventLike) -> None:
        super().listen(event)
        if self.dialog_activated:
            self.input_box.listen(event)
            self.prompt_box.listen(event)

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
