# ActReceiveCountSendFeed.py  08/08/2014  D.J.Whale
#
# Publish an actuator that can be remotely controlled.
# When this actuator is 'poked', count it.
# when a number of pokes has been met,
# send this on a separate feed that can be consumed by others.

import IoticLabs.JoinIOT as IOT
import time

MY_NAME     = "ActReceiveCountSendFeed"
MY_ACTUATOR = "printme_after" + str(COUNT_LIMIT)
MY_FEED     = "poked_" + str(COUNT_LIMIT) + "_times"

COUNT_LIMIT = 10
  
  
IOT.joinAs(MY_NAME)

count = 0

def justPoked(actuator, value):
  # when new data is received, it calls this function
  global count
  count = count + 1
  if count >= COUNT_LIMIT:
    print("10 pokes")
    count = 0
    pokeCounter.send("Poked " + str(COUNT_LIMIT))
  
IOT.reveal(MY_ACTUATOR, incoming=justPoked)
pokeCounter = IOT.advertise(MY_FEED)

IOT.loop()
IOT.leave()

# END
