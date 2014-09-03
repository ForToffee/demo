# ButtonFeedSend.py  08/08/2014  D.J.Whale
#
# Press a hardware button, sensed by GPIO.
# Sends this to a feed for others to use

import IoticLabs.JoinIOT as IOT
import time
import RPi.GPIO as GPIO

MY_NAME = "ButtonFeedSend"
MY_FEED = "button"

BUTTON = 10
POLL_TIME = 0.5


IOT.joinAs(MY_NAME)
button = IOT.advertise(MY_FEED)

GPIO.setmode(GPIO.BCM)

def main():
  last_b = False
  GPIO.setup(BUTTON, GPIO.IN)
  
  while True:
    time.sleep(POLL_TIME)
    b = GPIO.input(BUTTON)
    if b != last_b:
      print("sending")
      last_b = b
      button.tell(b)
    
try:
  main()
finally:
  GPIO.cleanup()
  IOT.leave()
  
# END


  
