# ActReceiveLED.py  08/08/2014  D.J.Whale
#
# Publishes an actuator
# When this actuator is poked, turns the LED on and off

import IoticLabs.JoinIOT as IOT
from config import *
import time
import RPi.GPIO as GPIO
from pibrella import *

MY_NAME        = MY_COMPUTER + "_ActReceiveLED"
MY_ACTUATOR    = "led"
THEIR_COMPUTER = "IOT_Pi_2"
THEIR_NAME     = THEIR_COMPUTER + "_demo"


IOT.joinAs(MY_NAME)

GPIO.setmode(GPIO.BCM)
GPIO.setup(RED_LED, GPIO.OUT)

def newData(actuator, value):
  print("data:" + str(value))
  state = actuator.isTrue(value)
  GPIO.output(RED_LED, state)
  
IOT.reveal(MY_ACTUATOR, incoming=newData)

IOT.loop()

IOT.cleanup()
GPIO.cleanup()

# END
