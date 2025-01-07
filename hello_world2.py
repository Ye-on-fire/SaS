import pygame
from pygame.transform import scale

from base.constants import EventCode
import utils
import game_constants as c
from game_collections import (
    EventLike,
    Core,
    ResourceManager,
    generate_imageset,
    listening,
    EntityLike,
    GroupLike,
    SceneLike,
    State,
    AnimatedSprite,
    generate_imageset_for_mac,
    Tile,
    SceneManager,
)
from game_objects import Player, Skeleton
from scenes import *

import pygame

if __name__ == "__main__":
    co = Core()
    player = Player(post_api=co.add_event)
    mapgen = MapGenerator(
        width=50,
        height=40,
        scale=3,
        path="./assets/mytiles/grassland/",
        core=co,
        player=player,
        enemy_amount=1,
        obstacle_amount=5,
    )
    scene = mapgen.generate_random_battle_ground([Skeleton])
    scenemanager = SceneManager(co.add_event, {"battleground": scene}, "battleground")
    resoucemanager = ResourceManager(co.add_event)

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
        elif ckeys[pygame.K_o]:
            co.add_event(
                EventLike(
                    c.SceneEventCode.RESTART,
                    body={
                        "scene_name": "battleground",
                        "pre_loaded_scene": mapgen.generate_random_battle_ground(
                            [Skeleton]
                        ),
                    },
                )
            )
        else:
            e = EventLike(
                c.StateEventCode.CHANGE_STATE,
                prior=100,
                body={"state": State.create_idle()},
                receivers=set([player.uuid]),
            )
            co.add_event(e)
        co.add_event(EventLike.anim_step_event(co.tick()))
        for event in co.yield_events():
            resoucemanager.listen(event)
            scenemanager.listen(event)
        co.flip()  # 更新屏幕缓冲区
        co.tick(60)
