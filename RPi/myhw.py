# myhw.py  - simple abstraction of some mock test hardware.

import random

def trace(msg):
  print("myhw:" + str(msg))
  
  
def buttonPressed(n):
  """Poll the present state of a button"""
  trace("poll button")
  v = random.randint(0,1)
  return (v==1)
  
b = False
def checkButton(n):
  """Check to see if a button state has changed since last call"""
  global b
  trace("checkButton")
  b = not b
  return b
  
  
def setLED(id, value):
  trace("setLED:" + str(id) + "=" + str(value))
  
# END

