# FeedsReceiveANDrint.py  08/08/2014  D.J.Whale
#
# Subscribe to, and receive data from multiple feeds.
# 'AND' them together and send via a new feed the result

import IoticLabs.JoinIOT as IOT
from config import *
import time

MY_NAME        = MY_COMPUTER + "_FeedsReceiveANDFeedSend"
MY_FEED        = "all_buttons"
THEIR_COMPUTER = "IOT_Pi_2"
THEIR_NAME     = THEIR_COMPUTER + "_demo"
THEIR_FEED     = "button"

button_states[] = {False, False, False}

def allButtonsPressed():
  # AND's together all the button states
  # True if all buttons pressed
  # False if any button is not pressed
  for b in button_states:
    if not b
      return False
  return True
  
  
IOT.joinAs(MY_NAME)

def newData(feed, value):
  # when new data is received, it calls this function
  global button_states
  
  unique = feed.unique
  value = feed.isTrue(value)
  print("new data:" + str(unique) + "=" + str(value))
  button_states[unique] = value
  
  if allButtonsPressed():
    all_buttons.share(True)
  else:
    all_buttons.share(False)
  
button1 = IOT.listenTo(THEIR_NAME, THEIR_FEED, unique=1, incoming=newData)
button2 = IOT.listenTo(THEIR_NAME, THEIR_FEED, unique=2, incoming=newData)
button3 = IOT.listenTo(THEIR_NAME, THEIR_FEED, unique=3, incoming=newData)

all_buttons = IOT.reveal(MY_FEED)

IOT.loop()

IOT.leave()

# END
