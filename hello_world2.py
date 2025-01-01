import pygame

from base.constants import EventCode
import utils
import game_constants as c
from game_collections import (
    EventLike,
    Core,
    listening,
    EntityLike,
    GroupLike,
    SceneLike,
)
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
    player = Player(post_api=co.add_event)
    wall = StaticObject(
        image=pygame.image.load("./assets/tiles/tree.png"),
        post_api=co.add_event,
    )
    wall.rect.x = 300
    wall.rect.y = 300
    scene1 = SceneLike(core=co)
    scene1.add_listener(player)
    scene1.add_listener(wall)
    scene1.layers[0] = []
    scene1.layers[0].append(player)
    scene1.layers[0].append(wall)

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
            scene1.listen(event)
        co.flip()  # 更新屏幕缓冲区
        co.tick(60)
