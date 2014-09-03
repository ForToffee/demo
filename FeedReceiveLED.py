# FeedReceiveLED.py  08/08/2014  D.J.Whale
#
# subscribes to a feed of data
# Turns the LED on and off depending on the feed data

import IoticLabs.JoinIOT as IOT
import time
import RPi.GPIO as GPIO

MY_NAME    = "FeedReceiveLED"
THEIR_NAME = "demo"
THEIR_FEED = "button"

LED = 11
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED, GPIO.OUT)

IOT.joinAs(MY_NAME)

def newData(feed, value):
  print("newData:" + str(value))
  state = feed.isTrue(value)
  GPIO.output(LED, state)
  
some_data = IOT.listenTo(THEIR_NAME, THEIR_FEED, incoming=newData)

IOT.loop()

IOT.cleanup()

# END
