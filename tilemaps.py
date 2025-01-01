import pygame

import utils
import game_constants as c
from game_collections import EventLike, Core, listening, EntityLike, GroupLike
import os


class Tile(EntityLike):
    def __init__(self, post_api, image, rect: pygame.Rect = None):
        rect: pygame.Rect = image.get_rect()
        super().__init__(post_api=post_api, rect=rect, image=image)

    @property
    def width(self):  # 获得tile的宽度
        return self.rect.get_width()

    @property
    def height(self):  # 获得tile的长度
        return self.rect.get_height()

    @property
    def tile_cord(self) -> tuple[int, int]:  # 可以把当前的贴图坐标计算出来
        return (self.rect.left // self.width, self.rect.top // self.height)

    @tile_cord.setter
    def tile_cord(
        self, new_cord: tuple[int, int]
    ):  # 可以通过贴图坐标直接自动设置rect的位置
        self.rect.left = new_cord[0] * self.width
        self.rect.top = new_cord[1] * self.height


class Wall(Tile):
    def __init__(self, post_api, image):
        rect = image.get_rect()
        super().__init__(post_api=post_api, rect=rect, image=image)

    @listening(c.MoveEventCode.MOVEATTEMPT)
    def judge_move(self, event):  # 比tile多了一个检测碰撞的机制
        offset = event.body["move_offset"]
        new_rect = event.body["original_pos"].copy()
        move_rect = event.body["original_pos"].copy()
        move_rect.x += offset.x
        move_rect.y += offset.y
        new_rect.x += offset.x
        if self.rect.colliderect(new_rect):
            move_rect.x -= offset.x
        new_rect.x -= offset.x
        new_rect.y += offset.y
        if self.rect.colliderect(new_rect):
            move_rect.y -= offset.y
        self.post(
            EventLike(
                c.MoveEventCode.MOVEALLOW,
                sender=self.uuid,
                body={"pos": move_rect},
                receivers={event.sender},
            )
        )
