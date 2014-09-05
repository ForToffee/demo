# RepeatingLED.py  08/08/2014  D.J.Whale
#
# Generates a repeating time interval.
# Uses this to flash an LED on the GPIO pins

import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

LED = 11
REPEAT_TIME = 1

def main():
  GPIO.setup(LED, GPIO.OUT)
  state = True
  
  while True:
    GPIO.output(LED, state)
    time.sleep(REPEAT_TIME)
    state = not state
    
try:
  main()
finally:
  GPIO.cleanup()
  
  
