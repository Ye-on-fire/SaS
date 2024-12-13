import pygame
import sys
import math

screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
playerpos = pygame.Vector2(1280//2,720//2)
mousepos = (0,0)
move_not_completed = False
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
    
    screen.fill('blue')
    pygame.draw.circle(screen, 'red', playerpos, 40.0)
    
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
    


    pygame.display.flip()

    deltatime = clock.tick(120) / 1000
