# FeedReceivePrint.py  08/08/2014  D.J.Whale
#
# Subscribe to, and receive data from a feed.
# Print this data on the screen.

import IoticLabs.JoinIOT as IOT
from config import *

MY_NAME        = MY_COMPUTER + "_ClockWatcher"
THEIR_COMPUTER = "IOT_Pi_2"
THEIR_NAME     = "Clock"
THEIR_FEED     = "tick"

IOT.joinAs(MY_NAME)

def newData(feed, value):
  # when new data is received, it calls this function
  print("from: " + feed.originator + " new data:" + str(value))
  
tick = IOT.listenTo(THEIR_NAME, THEIR_FEED, incoming=newData)

IOT.loop()
IOT.leave()
  
# END

