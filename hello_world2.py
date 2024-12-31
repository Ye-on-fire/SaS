import pygame

from base.constants import EventCode
import utils
import game_constants as c
from game_collections import EventLike, Core, listening, EntityLike, GroupLike
from custom_collections import (
    State,
    AnimatedSprite,
    generate_imageset_for_mac,
    Player,
    StaticObject,
)

import pygame

if __name__ == "__main__":
    co = Core()
    group_player = GroupLike()
    group_player.add_listener(Player(post_api=co.add_event))
    group_walls = GroupLike()
    wall = StaticObject(
        image=pygame.image.load("./assets/tiles/tree.png"),
        post_api=co.add_event,
    )
    wall.rect.x = 300
    wall.rect.y = 300
    group_walls.add_listener(wall)
    while True:
        co.window.fill((0, 0, 0))  # 全屏涂黑
        ckeys = pygame.key.get_pressed()
        if (
            ckeys[pygame.K_a]
            or ckeys[pygame.K_w]
            or ckeys[pygame.K_d]
            or ckeys[pygame.K_s]
        ):
            e = EventLike(c.MoveEventCode.PREMOVE, prior=100, body={})
            co.add_event(e)
        else:
            e = EventLike(
                c.StateEventCode.CHANGE_STATE,
                prior=100,
                body={"state": State.create_idle()},
            )
            co.add_event(e)
        co.add_event(EventLike.anim_step_event(co.time_ms))
        co.add_event(EventLike.step_event(co.time_ms))
        co.add_event(EventLike.draw_event(co.window))
        for event in co.yield_events():
            group_walls.listen(event)
            group_player.listen(event)  # 听取: 核心事件队列

        co.flip()  # 更新屏幕缓冲区
        co.tick(60)
