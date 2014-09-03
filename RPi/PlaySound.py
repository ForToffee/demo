# PlaySound.py  12/08/2014  D.J.Whale
#
# Play a wav file through the speaker
#
# remember:
# for audio jack:
#   sudo amixer cset numid=3 1
# for max volume
#   sudo amixer cset numid=3 100%

import pygame
import time

pygame.mixer.init()
bell = pygame.mixer.sound("sounds/doorbell.wav")

while True:
  bell.play()
  time.sleep(4)
  
