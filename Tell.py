# Tell.py  05/09/2014  D.J.Whale
#
# Tells a revealed actuator to do something.
#
# This script is designed to run on the Raspberry Pi only

import IoticLabs.JoinIOT as IOT
from config import *
import time
import RPi.GPIO as GPIO
from pibrella import *
import pygame


MY_NAME        = MY_COMPUTER + "_Tell"
THEIR_COMPUTER = "IOT_Pi_2"
THEIR_NAME     = THEIR_COMPUTER + "_Reveal"
THEIR_ACTUATOR = "LED"

POLL_TIME = 0.5

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON, GPIO.IN)

pygame.mixer.init()
sound = pygame.mixer.Sound("sounds/accessd.wav")

IOT.joinAs(MY_NAME)
led = IOT.attachTo(THEIR_NAME, THEIR_ACTUATOR)


def main():
  b = False
  
  while True:
    time.sleep(POLL_TIME)
    if GPIO.input(BUTTON) == True:
      if not b:
        print("pressed")
        sound.play()
        led.tell(b) 
        b = True
    else:
      if b:
        print("released")
        b = False
    
try:
  main()
finally:
  GPIO.cleanup()
  IOT.leave()

# END
  
  
