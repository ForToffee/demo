# Reveal.py  05/09/2014  D.J.Whale
#
# Reveals an LED so it can be remotely controlled.
#
# This script is designed only for the Raspberry Pi 

import IoticLabs.JoinIOT as IOT
from config import *
import time
import RPi.GPIO as GPIO
from pibrella import *
import pygame


MY_NAME        = MY_COMPUTER + "_Reveal"
MY_ACTUATOR    = "LED"

GPIO.setmode(GPIO.BCM)
GPIO.setup(RED_LED, GPIO.OUT)
GPIO.output(RED_LED, False)

pygame.mixer.init()
sound = pygame.mixer.Sound("sounds/is_cow_moo.wav")

IOT.joinAs(MY_NAME)


def newData(actuator, value):
  print("data:" + str(value))
  #state = actuator.isTrue(value)
  sound.play()
  GPIO.output(RED_LED, True)
  time.sleep(0.5)
  GPIO.output(RED_LED, False)

  
IOT.reveal(MY_ACTUATOR, incoming=newData)
IOT.loop()

IOT.cleanup()
GPIO.cleanup()

# END
