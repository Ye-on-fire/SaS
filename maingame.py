import pygame
import sys
import math
#你好hello
sc_width,sc_height = 1280,720
screen = pygame.display.set_mode((sc_width,sc_height))
clock = pygame.time.Clock()
playerpos = pygame.Vector2(sc_width//2,sc_height//2)
mousepos = (0,0)

ch_image = pygame.image.load('./ch.jpg')
bg = pygame.image.load('./bg.jpg')
# move_not_completed = False
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    #     if event.type == pygame.MOUSEBUTTONDOWN:
    #         mouseclick = pygame.mouse.get_pressed()
    #         if mouseclick[0]:
    #             mousepos = pygame.mouse.get_pos()
    #             v_x = 300*math.cos(math.atan2((mousepos[1]-playerpos.y),(mousepos[0]-playerpos.x)))
    #             v_y = 300*math.sin(math.atan2((mousepos[1]-playerpos.y),(mousepos[0]-playerpos.x)))
    #             move_not_completed = True
    # if move_not_completed:
    #     playerpos.x += v_x*deltatime
    #     playerpos.y += v_y*deltatime
    #     if abs(playerpos.x-mousepos[0])<=1.5 and abs(playerpos.y-mousepos[1]) <= 1.5:
    #         move_not_completed = False
    
    screen.blit(bg,(0,0))
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        playerpos.y -= 300 * deltatime
    if keys[pygame.K_s]:
        playerpos.y += 300 * deltatime
    if keys[pygame.K_a]:
        playerpos.x -= 300 * deltatime
    if keys[pygame.K_d]:
        playerpos.x += 300 * deltatime
    if keys[pygame.K_ESCAPE]:
        pygame.quit()
        sys.exit()
    screen.blit(ch_image,playerpos)


    pygame.display.flip()

    deltatime = clock.tick(120) / 1000
