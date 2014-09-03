# ActReceiveLED.py  08/08/2014  D.J.Whale
#
# Publishes an actuator
# When this actuator is poked, turns the LED on and off

import IoticLabs.JoinIOT as IOT
import time
import RPi.GPIO as GPIO

MY_NAME     = "ActReceiveLED"
MY_ACTUATOR = "led"
THEIR_NAME  = "demo"

LED = 11


IOT.joinAs(MY_NAME)

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED, GPIO.OUT)

def newData(actuator, value):
  print("data:" + str(value))
  state = actuator.isTrue(value)
  GPIO.output(LED, state)
  
IOT.reveal(MY_ACTUATOR, incoming=newData)

IOT.loop()

IOT.cleanup()
GPIO.cleanup()

# END
