# Listen.py  05/09/2014  D.J.Whale
#
# Listen to a feed of data, and pulse the LED every time data arrives
#
# This is designed to work on the Raspberry Pi only

import IoticLabs.JoinIOT as IOT
from config import *
import RPi.GPIO as GPIO
from pibrella import *
import time


MY_NAME        = MY_COMPUTER + "_Listen"
THEIR_COMPUTER = "IOT_Pi_2"
THEIR_NAME     = THEIR_COMPUTER + "_Advertise"
THEIR_FEED     = "pressed"

GPIO.setmode(GPIO.BCM)
GPIO.setup(RED_LED, GPIO.OUT)
GPIO.output(RED_LED, False)


IOT.joinAs(MY_NAME)

def newData(feed, value):
  # when new data is received, it calls this function
  print("from: " + feed.originator + " new data:" + str(value))
  GPIO.output(RED_LED, True)
  time.sleep(0.25)
  GPIO.output(RED_LED, False)

  
pressed = IOT.listenTo(THEIR_NAME, THEIR_FEED, incoming=newData)

IOT.loop()
IOT.leave()
  
# END

