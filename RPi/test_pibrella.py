# test_pibrella.py  05/09/2014  D.J.Whale

from pibrella import *
import RPi.GPIO as GPIO
import time


INPUTS = [BUTTON, IN_A, IN_B, IN_C, IN_D]
OUTPUTS = [RED_LED, YELLOW_LED, GREEN_LED, BEEP, OUT_E, OUT_F, OUT_G, OUT_H]


GPIO.setmode(GPIO.BCM)

for g in INPUTS:
  GPIO.setup(g, GPIO.IN)

for g in OUTPUTS:
  GPIO.setup(g, GPIO.OUT)


def main():
  b = False

  while True:
    for g in OUTPUTS:
      GPIO.output(g, True)
    time.sleep(0.5)

    for g in OUTPUTS:
      GPIO.output(g, False)
    time.sleep(0.5)

    if GPIO.input(BUTTON) == True:
      if not b:
        print("Button PRESS")
        b = True
    else:
      if b:
        print("Button RELEASED")
        b = False

try:
  main()
finally:
  GPIO.cleanup()

# END




