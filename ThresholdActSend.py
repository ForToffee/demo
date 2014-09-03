# ThresholdActSend.py  08/08/2014  D.J.Whale
#
# A repeating interval is generated.
# Sends this to a remote actuator, which does someting with it

import IoticLabs.JoinIOT as IOT
import time

MY_NAME        = "ThresholdActSend"
THEIR_NAME     = "demo"
THEIR_ACTUATOR = "useValue"

THRESHOLD      = 50

IOT.joinAs(MY_NAME)
useValue = IOT.attachTo(THEIR_NAME, THEIR_ACTUATOR)

def main():
  value = raw_input("value? ") # python2
  #value = input("value? ") #python3
  
  if value > THRESHOLD:
    print("sending")
    useValue.tell(value)
   
try:
  main()
finally:
  IOT.leave()
  
# END

  
