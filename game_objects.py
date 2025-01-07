import collections
from turtle import width

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
from game_collections import *

"""
该文件是基于game_collections中的基类更加具体的游戏内物体
包括Player，Enemy之类的
"""


class Player(AnimatedSprite):
    """
    游戏角色类，包含对角色移动，动作，动画的控制
    """

    def __init__(self, post_api):
        if c.PLATFORM == "Darwin":
            imageset = generate_imageset_for_mac("./assets/player/")
        else:
            imageset = generate_imageset("./assets/player/")
        image = imageset["idle"][0][0]
        super().__init__(image=image, imageset=imageset, post_api=post_api)
        self.rect = pygame.Rect(0, 0, 63, 114)  # width 21*3 height 38*3
        self.rect.center = (500, 500)
        self.hp = 100
        self.damage = 10
        self.attack_range = [150, 114]

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
            # if (
            #     self.state.info["frame_type"][self.current_frame] == 1
            #     and self.first_frame
            # ):
            #     self.first_frame = False
            #     if self.faceing == 0:  # 设定攻击的范围
            #         attack_rect = pygame.Rect(
            #             self.rect.centerx,
            #             self.rect.centery - self.rect.height // 2,
            #             *self.attack_range,
            #         )
            #     else:
            #         attack_rect = pygame.Rect(
            #             self.rect.centerx - self.attack_range[0],
            #             self.rect.centery - self.rect.height // 2,
            #             *self.attack_range,
            #         )
            #     self.post(
            #         EventLike(
            #             c.BattleCode.PLAYERATTACK,
            #             sender=self.uuid,
            #             body={"rect": attack_rect, "damage": self.damage},
            #         )
            #     )
            #

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


class Skeleton(AnimatedSprite):
    def __init__(
        self,
        imageset=generate_imageset("./assets/skeleton/"),
        state: State = State.create_idle(),
        direction=0,
        post_api=None,
        hp=30,
        damage=10,
        money_drop=10,
    ):
        image = imageset["idle"][0][0]
        super().__init__(imageset, image, state, direction, post_api)
        self.hp = hp
        self.damage = damage
        self.money_drop = money_drop

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
            print(self.hp)
        if self.hp <= 0:
            self.change_state(State.create_die())
            self.post(
                EventLike(c.ResourceCode.CHANGEMONEY, body={"money": self.money_drop})
            )
