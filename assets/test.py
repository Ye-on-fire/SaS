import os
import pygame


def generate_imageset(path):
    imageset = {}
    for i in os.listdir(path):
        temp = [[], []]
        for j in os.listdir(os.path.join(path, i)):
            image = pygame.image.load(os.path.join(path, i, j))
            image_left = pygame.transform.flip(image, 1, 0)
            temp[0].append(image)
            temp[1].append(image_left)
        imageset[i] = temp
    return imageset


pygame.init()
print(generate_imageset("./player/"))
