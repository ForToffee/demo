# RepeatingFeedSend.py  08/08/2014  D.J.Whale
#
# Generates a repeating time interval.
# Uses this to send feed data to the IOT

import IoticLabs.JoinIOT as IOT
from config import *
import time

MY_NAME     = MY_COMPUTER + "_Clock"
MY_FEED     = "tick"
REPEAT_TIME = 1


IOT.joinAs(MY_NAME)
clock = IOT.advertise(MY_FEED)

def main():
  tickCount = 1
  
  while True:
    print("sending:" + str(tickCount))
    clock.share(str(tickCount))
    tickCount += 1
    time.sleep(REPEAT_TIME)
    
try:
  main()
finally:
  IOT.leave()
  
# END

  
