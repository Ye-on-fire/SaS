import pygame
import sys
import math


def is_on_bottom(obj, bottom):
    if obj.bottom >= bottom:
        return True
    return False


# 你好hello
sc_width, sc_height = 800, 600
screen = pygame.display.set_mode((sc_width, sc_height))
clock = pygame.time.Clock()
gravity = 98
mousepos = (0, 0)

deltatime = 0
ch_image = pygame.image.load("./ch.png")
bg = pygame.image.load("./bg.jpg")
playerpos = ch_image.get_rect()
playerpos.center = (sc_width // 2, sc_height // 2)
playervel = pygame.Vector2(0, 0)
# move_not_completed = False
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                if is_on_bottom(playerpos, sc_height):
                    print(is_on_bottom(playerpos, sc_height))
                    playervel.y = -2000

    screen.blit(bg, (0, 0))
    keys = pygame.key.get_pressed()
    if keys[pygame.K_a]:
        playerpos.left -= 600 * deltatime
    if keys[pygame.K_d]:
        playerpos.left += 600 * deltatime
    if keys[pygame.K_ESCAPE]:
        pygame.quit()
        sys.exit()
    if playerpos.bottom >= sc_height:
        playerpos.bottom = sc_height
        # playervel.y = 0
    else:
        playervel.y += gravity
    screen.blit(ch_image, playerpos)
    playerpos.y += playervel.y * deltatime

    pygame.display.flip()

    deltatime = clock.tick(120) / 1000
