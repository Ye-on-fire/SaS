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
)
from game_objects import Player, Skeleton
from scenes import *

import pygame


class MainGame:
    def __init__(self) -> None:
        self.co = Core()
        self.player = Player(post_api=self.co.add_event)
        self.mapgenerator = MapGenerator(scale=3, core=self.co, player=self.player)
        self.scenemanager = SceneManager(
            self.co.add_event,
            {"home": Home(core=self.co, player=self.player)},
            "home",
            self.mapgenerator,
        )
        self.resourcemanager = ResourceManager(self.co.add_event)

    def reset(self):
        self.player = Player(post_api=self.co.add_event)
        self.mapgenerator = MapGenerator(scale=3, core=self.co, player=self.player)
        self.scenemanager = SceneManager(
            self.co.add_event,
            {"home": Home(core=self.co, player=self.player)},
            "home",
            self.mapgenerator,
        )
        self.resourcemanager = ResourceManager(self.co.add_event)

    def run(self):
        while True:
            self.co.window.fill("black")  # 全屏涂黑
            ckeys = pygame.key.get_pressed()
            if (
                ckeys[pygame.K_a]
                or ckeys[pygame.K_w]
                or ckeys[pygame.K_d]
                or ckeys[pygame.K_s]
            ):
                e = EventLike(c.MoveEventCode.PREMOVE, prior=100, body={})
                self.co.add_event(e)
            elif ckeys[pygame.K_o]:
                self.co.add_event(
                    EventLike(
                        c.SceneEventCode.RESTART,
                        body={
                            "scene_name": "battleground",
                            "pre_loaded_scene": self.mapgenerator.generate_random_battle_ground(
                                [Skeleton]
                            ),
                        },
                    )
                )
            elif ckeys[pygame.K_r]:
                self.reset()
            else:
                e = EventLike(
                    c.StateEventCode.CHANGE_STATE,
                    prior=100,
                    body={"state": State.create_idle()},
                    receivers=set([self.player.uuid]),
                )
                self.co.add_event(e)
            self.co.add_event(EventLike.anim_step_event(self.co.tick()))
            for event in self.co.yield_events():
                self.resourcemanager.listen(event)
                self.scenemanager.listen(event)
            self.co.flip()  # 更新屏幕缓冲区
            self.co.tick(60)


if __name__ == "__main__":
    maingame = MainGame()
    maingame.run()