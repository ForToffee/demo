# RepeatingActSend.py  08/08/2014  D.J.Whale
#
# Generates a repeating time interval.
# Uses this to remotely actuate something on the IOT

import IoticLabs.JoinIOT as IOT

import time

MY_NAME        = "RepeatingActSend"
THEIR_NAME     = "ActReceiver"
THEIR_ACTUATOR = "doSomething"
REPEAT_TIME    = 1

IOT.joinAs(MY_NAME)
doSomething = IOT.attachTo(THEIR_NAME, THEIR_ACTUATOR)

def main():
  state = True
  count = 0
  
  while True:
    time.sleep(REPEAT_TIME)
    count += 1
    print("sending:" + str(count))
    doSomething.tell(state)
    state = not state
 
try:
  main()
finally:
  IOT.leave()

# END
