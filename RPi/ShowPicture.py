# ShowPicture.py  12/08/2014  D.J.Whale
#
# from: http://blog.whaleygeek.co.uk/controlling-the-raspberry-pi-camera-with-python/

import time
import pygame

WIDTH      = 100
HEIGHT     = 100
FONTSIZE   = 50
IMAGE_NAME = "image.gif"
TEXT       = "Visitor!"

# BUILD A SCREEN
pygame.init()
screen = pygame.display.set_mode((WIDTH,HEIGHT))
black = pygame.Color(0, 0, 0)
textcol = pygame.Color(255, 255, 0)
screen.fill(black)
pygame.display.update()    

#READ IMAGE AND PUT ON SCREEN
img = pygame.image.load('image.gif')
screen.blit(img, (0, 0))

#OVERLAY CAPTIONS AS TEXT
text = MESSAGE
font = pygame.font.Font('freesansbold.ttf', FONTSIZE)
font_surf = font.render(text, True, textcol)
font_rect = font_surf.get_rect()
font_rect.left = 5
font_rect.top = 5
screen.blit(font_surf, font_rect)
pygame.display.update()

# WAIT A BIT
sleep(3)

# CLOSE CLEANLY AND EXIT
pygame.quit()

