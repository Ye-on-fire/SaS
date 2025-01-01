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
    State,
    AnimatedSprite,
    generate_imageset_for_mac,
    Player,
    Tile,
)

import pygame

if __name__ == "__main__":
    co = Core()
    player = Player(post_api=co.add_event)
    scene1 = SceneLike(core=co)
    scene1.load_tilemap("./maps/1.json")
    scene1.add_listener(player)
    scene1.layers[1] = []
    scene1.layers[1].append(player)

    while True:
        co.window.fill("black")  # 全屏涂黑
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
        for event in co.yield_events():
            scene1.listen(event)
        co.flip()  # 更新屏幕缓冲区
        co.tick(60)
