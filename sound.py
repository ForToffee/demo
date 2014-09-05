# sound.py  05/09/2014  D.J.Whale
#
# An example of how to play a sound file on the Raspberry Pi

import pygame


pygame.mixer.init()
sound = pygame.mixer.Sound("sounds/is_cat_meow.wav")
sound.play()

raw_input("Was that fun?!")


