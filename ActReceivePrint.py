# ActReceivePrint.py  08/08/2014  D.J.Whale
#
# Publish an actuator that can be remotely controlled.
# When this actuator is 'poked', print a message


import IoticLabs.JoinIOT as IOT
import time

MY_NAME     = "ActReceivePrint"
MY_ACTUATOR = "doSomething"
  
IOT.joinAs(MY_NAME)

def justPoked(actuator, value):
  # when new data is received, it calls this function
  print("FROM: " + actuator.originator + " DATA:" + str(value))
    
IOT.reveal(MY_ACTUATOR, incoming=justPoked)

IOT.loop()

IOT.cleanup()

# END
