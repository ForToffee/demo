# ButtonPrint.py  08/08/2014  D.J.Whale
#
# Press a hardware button, sensed by GPIO.
# Prints a message on screen only when the button changes.

import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

BUTTON = 10
POLL_TIME = 0.5

def main():
  last_b = False
  GPIO.setup(BUTTON, GPIO.IN)
  
  while True:
    time.sleep(POLL_TIME)
    b = GPIO.input(BUTTON)
    if b != last_b:
      last_b = b
      print("button" + str(b)
    
try:
  main()
finally:
  GPIO.cleanup()
  
  
