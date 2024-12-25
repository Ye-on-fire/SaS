"""
原点在屏幕左上角, 往右为x轴正方向, 往下为y轴正方向。
各种实体的Rect的坐标也是默认为左上角。
"""

import pygame

from base.constants import EventCode
import utils
import game_constants as c
from game_collections import EventLike, Core, listening, EntityLike, GroupLike
from custom_collections import State, AnimatedSprite, generate_imageset

import pygame


# class Mob(EntityLike):
#     def __init__(
#         self,
#         rect: pygame.Rect = pygame.Rect(610, 330, 60, 60),  # x, y, width, height
#     ):
#         image = utils.load_image_and_scale(r".\assets\npc\monster\1.png", rect)
#         super().__init__(rect, image=image)
#
#     @listening(pygame.KEYDOWN)  # 捕获: 按下按键
#     def move(self, event: EventLike):
#         keys = pygame.key.get_pressed()
#         if keys[pygame.K_w]:  # w被按下
#             self.rect.y -= 50  # y坐标减少10
#         if keys[pygame.K_a]:
#             self.rect.x -= 50
#         if keys[pygame.K_s]:
#             self.rect.y += 50
#         if keys[pygame.K_d]:
#             self.rect.x += 50


class Mob(AnimatedSprite):
    def __init__(self):
        imageset = generate_imageset("./assets/player/")
        image = imageset["idle"][0][0]
        super().__init__(image=image, imageset=imageset)
        self.rect.center = (500, 500)

    @listening(c.TempTestCode.MOVE)
    def move(self, event):
        state = State("run", duration=5)
        self.change_state(state)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.faceing = 1
            self.rect.x -= 5
        if keys[pygame.K_d]:
            self.faceing = 0
            self.rect.x += 5
        if keys[pygame.K_w]:
            self.rect.y -= 5
        if keys[pygame.K_s]:
            self.rect.y += 5


if __name__ == "__main__":
    co = Core()
    group = GroupLike()
    group.add_listener(Mob())
    group.add_listener(
        EntityLike(
            pygame.Rect(410, 330, 60, 60),
            image=utils.load_image_and_scale(
                r".\assets\tiles\tree.png", pygame.Rect(510, 330, 60, 60)
            ),
        )
    )

    while True:
        co.window.fill((0, 0, 0))  # 全屏涂黑
        ckeys = pygame.key.get_pressed()
        if (
            ckeys[pygame.K_a]
            or ckeys[pygame.K_w]
            or ckeys[pygame.K_d]
            or ckeys[pygame.K_s]
        ):
            e = EventLike(c.TempTestCode.MOVE, prior=100, body={})
            co.add_event(e)
        else:
            e = EventLike(
                c.StateEventCode.CHANGE_STATE,
                prior=100,
                body={"state": State.create_idle()},
            )
            co.add_event(e)
        co.add_event(EventLike.step_event(secord=0))
        for event in co.yield_events():
            group.listen(event)  # 听取: 核心事件队列

        co.flip()  # 更新屏幕缓冲区
        co.tick(60)
