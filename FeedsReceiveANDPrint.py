# FeedsReceiveANDrint.py  08/08/2014  D.J.Whale
#
# Subscribe to, and receive data from multiple feeds.
# 'AND' them together and display a message if they are all True

import IoticLabs.JoinIOT as IOT
import time

MY_NAME    = "FeedsReceiveANDPrint"
THEIR_NAME = "demo"
THEIR_FEED = "button"

button_states = {}

def allButtonsPressed():
  # AND's together all the button states
  # True if all buttons pressed
  # False if any button is not pressed
  for b in button_states:
    if not b:
      return False
  return True
  
  
IOT.joinAs(MY_NAME)

def newData(feed, value):
  # when new data is received, it calls this function
  global button_states
  
  unique = feed.unique
  value = feed.isTrue(value)
  print("from: " + feed.originator + " new feed data:" + str(unique) + "=" + str(value))
  button_states[unique] = value
  
  if allButtonsPressed():
    print("All buttons are pressed")
  else:
    print("Some buttons are not pressed any more")
  
button1 = IOT.listenTo(THEIR_NAME, THEIR_FEED, unique=1, incoming=newData)
button2 = IOT.listenTo(THEIR_NAME, THEIR_FEED, unique=2, incoming=newData)
button3 = IOT.listenTo(THEIR_NAME, THEIR_FEED, unique=3, incoming=newData)


IOT.loop()
IOT.leave()

# END
