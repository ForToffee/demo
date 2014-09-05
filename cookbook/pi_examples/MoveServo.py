# MoveServo.py  12/08/2014  D.J.Whale
#
# from: https://github.com/whaleygeek/pibakeoff/blob/master/code/ServoOutput.py


import RPi.GPIO as GPIO
import time

SERVO = 7

GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO, GPIO.OUT)

# SERVO PARAMETERS
# Short pulse: servo swings one way, long pulse: swings other way.
# The pulse width determines the servo's final position.
# Must repeat every 20ms

SHORTEST = 0.001    # 1ms    = 0.001s
LONGEST = 0.00225   # 2.25ms = 0.00225s
PERIOD = 0.02       # 20ms   = 0.02s
PULSES = 20         # number of pulses for a full movement

def PWM(ON, OFF):
  #(ON + OFF) must be = the repetiion rate: 20ms for this demo
  GPIO.output(SERVO, True)     
  time.sleep(ON)          # pulse width determines final position
  GPIO.output(SERVO ,False)
  time.sleep(OFF)         # makes up the remaining 20ms

#Function to send 20 pulses to the servo
# This gives servo time to get into position)
# Servo will jitter if you give it too little time

def servo(pulse):
  # pulse should be in the range 0.001 to 0.00225 seconds
  for pulseNumber in range(PULSES):
    PWM(pulse, PERIOD-PULSE)

#Main code
# Makes servo swing one way, wait, then the other
# Press Ctrl+c on keyboard to stop the code and exit properly
try:
  while True:     
    servo(LONGEST)
    time.sleep(1)
    servo(SHORTEST)
    time.sleep(1)
finally:
  GPIO.cleanup()




