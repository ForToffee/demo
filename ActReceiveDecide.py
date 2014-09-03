# ActReceiveDecide.py  08/08/2014  D.J.Whale
#
# Publish an actuator that can be remotely controlled.
# When this actuator is 'poked', if it has not been poked in the
# last 15 seconds then print a message. Otherwise, do nothing

import IoticLabs.JoinIOT as IOT
import time

MY_NAME = "ActReceiveDecide"
MY_ACTUATOR = "printme_every" + str(IGNORE_TIME)
IGNORE_TIME = 15

IOT.joinAs(MY_NAME)

lasttime = time.time()

def justPoked(actuator, value):
  global lasttime
  # when new data is received, it calls this function
  now = time.time()
  if now > lasttime + HOLDOFF:
    lasttime = now
    print("Not poked in last " + str(HOLDOFF) + " second(s)"
  
IOT.reveal(MY_ACTUATOR, incoming=justPoked)

IOT.loop()
IOT.leave()

# END
