import pygame

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
from game_objects import Player, Enemy

import pygame

if __name__ == "__main__":
    co = Core()
    player = Player(post_api=co.add_event)
    enemy = Enemy(
        post_api=co.add_event, imageset=generate_imageset("./assets/skeleton/")
    )
    enemy.rect.move_ip((300, 500))
    scene1 = SceneLike(core=co, name="1", player=player)
    scene1.load_tilemap("./maps/1.json")
    scene1.add_listener(player)
    scene1.layers[1].append(player)
    scene2 = SceneLike(core=co, name="2", player=player)
    scene2.load_tilemap("./maps/2.json")
    scene2.add_listener(player)
    scene2.add_listener(enemy)
    scene2.layers[1].append(player)
    scene2.layers[1].append(enemy)
    scenemanager = SceneManager(co.add_event, {"1": scene1, "2": scene2}, "1")
    resoucemanager = ResourceManager(co.add_event)
    # scene1.layers[1] = []

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
                    c.SceneEventCode.CHANGE_SCENE,
                    body={"scene_name": "2", "playerpos": (800, 500)},
                )
            )
        else:
            e = EventLike(
                c.StateEventCode.CHANGE_STATE,
                prior=100,
                body={"state": State.create_idle()},
            )
            co.add_event(e)
        co.add_event(EventLike.anim_step_event(co.time_ms))
        for event in co.yield_events():
            resoucemanager.listen(event)
            scenemanager.listen(event)
            scenemanager.current_scene.listen(event)
        co.flip()  # 更新屏幕缓冲区
        co.tick(60)
