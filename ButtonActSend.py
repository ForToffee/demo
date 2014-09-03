# ButtonActSend.py  08/08/2014  D.J.Whale
#
# Press a hardware button, sensed by GPIO.
# Sends this to a remote actuator, which does someting with it

import IoticLabs.JoinIOT as IOT
import time
import RPi.GPIO as GPIO

MY_NAME = "ButtonActSend"
THEIR_NAME = "demo"
THEIR_ACTUATOR = "pokeme"

BUTTON = 10
POLL_TIME = 0.5


IOT.joinAs(MY_NAME)
pokeme = IOT.attachTo(THEIR_NAME, THEIR_ACTUATOR)

GPIO.setmode(GPIO.BCM)

def main():
  last_b = False
  GPIO.setup(BUTTON, GPIO.IN)
  
  while True:
    time.sleep(POLL_TIME)
    b = GPIO.input(BUTTON)
    if b != last_b:
      last_b = b
      print("sending")
      pokeme.tell(b)
    
try:
  main()
finally:
  GPIO.cleanup()
  IOT.leave()
  
  
