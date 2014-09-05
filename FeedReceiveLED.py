# FeedReceiveLED.py  08/08/2014  D.J.Whale
#
# subscribes to a feed of data
# Turns the LED on and off depending on the feed data

import IoticLabs.JoinIOT as IOT
from config import *
import time
import RPi.GPIO as GPIO
from pibrella import *

MY_NAME        = MY_COMPUTER + "_FeedReceiveLED"
THEIR_COMPUTER = "IOT_Pi_2"
THEIR_NAME     = THEIR_COMPUTER + "demo"
THEIR_FEED     = "button"

GPIO.setmode(GPIO.BCM)
GPIO.setup(RED_LED, GPIO.OUT)

IOT.joinAs(MY_NAME)

def newData(feed, value):
  print("newData:" + str(value))
  state = feed.isTrue(value)
  GPIO.output(RED_LED, state)
  
some_data = IOT.listenTo(THEIR_NAME, THEIR_FEED, incoming=newData)

IOT.loop()

IOT.cleanup()

# END
