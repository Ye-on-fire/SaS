import pygame
import random
import sys
import time

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
    SceneManager,)

clock = pygame.time.Clock()

class Monster(AnimatedSprite):
    def __init__(self,post_api):
        imageset = generate_imageset_for_mac("./assets/player/")
        image = imageset["idle"][0][0]
        super().__init__(image=image, imageset=imageset, postapi= post_api)
        self.rect.center = (500, 500)
    
    @listening(c.EventCode.STEP)
    def move(self, event):
        self.rect.x += random.choice((-10,10))
        self.rect.y += random.choice((-10,10))
        
        
    @listening(pygame.QUIT)
    def quit_game(self, event):
        Core.exit()
        



if __name__ == "__main__":
    co = Core()
    monster = Monster(post_api=co.add_event)
    scene1 = SceneLike(core=co, name="1", player=monster)
    scene1.load_tilemap("./maps/1.json")
    scene1.add_listener(monster)
    scene1.layers[1].append(monster)
    scene2 = SceneLike(core=co, name="2", player=monster)
    scene2.load_tilemap("./maps/2.json")
    scene2.add_listener(monster)
    scene2.layers[1].append(monster)
    scenemanager = SceneManager(co.add_event, {"1": scene1, "2": scene2}, "1")
    # scene1.layers[1] = []  

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
    e = EventLike(c.MoveEventCode.PREMOVE, prior=100, body={})
    
    
    co.add_event(e)
    co.add_event(EventLike.anim_step_event(co.time_ms))
    co.add_event(EventLike.anim_step_event(co.time_ms))
    for event in co.yield_events():
        scenemanager.listen(event)
        scenemanager.current_scene.listen(event)
    co.flip()  # 更新屏幕缓冲区
    co.tick(60)

    


