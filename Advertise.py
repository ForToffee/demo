# Advertise.py  05/09/2014  D.J.Whale
#
# Advertise a feed of data, and share data via that advert.
# Every time you press the button, it shares "pressed" with a count value
#
# Designed only to run on the Raspberry Pi

import IoticLabs.JoinIOT as IOT
from config import *
import RPi.GPIO as GPIO
from pibrella import *
import time
#import pygame


MY_NAME     = MY_COMPUTER + "_Advertise"
MY_FEED     = "pressed"


GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON, GPIO.IN)

#pygame.mixer.init()
#sound = pygame.mixer.Sound("sounds/is_cow_moo.wav")

IOT.joinAs(MY_NAME)
pressed = IOT.advertise(MY_FEED)



def main():
  count = 0
  b = False
 
  while True:
    time.sleep(0.1)
    if GPIO.input(BUTTON) == True:
      if not b:
        count = count + 1
        print("pressed:" + str(count))
        #sound.play()
        pressed.share(str(count))
        b = True
    else:
      if b:
        print("released")
        b = False
    
try:
  main()
finally:
  IOT.leave()
  GPIO.cleanup()
  
# END

  
