# A simple example of using the IOT API's

# IMPORT ---------------------------------------------------------------

import IoticLabs.JoinIOT as IOT
import time
import myhw

MY_NAME = "Cookbook"


# JOIN -----------------------------------------------------------------

#join with a default name of your MAC addr, cached in iot.config
#IOT.join()

#join with a name
IOT.joinAs(MY_NAME)


#join with debug messages enabled
#IOT.join(debug=True)
#IOT.joinAs(MY_NAME, debug=True)

#at end of program
IOT.leave()

#If decomissioning the thing
#IOT.leave(permanent=True)


# PUBLISH ACTUATION ----------------------------------------------------

# the callback that handles remote actuation of our actuator
def changeMyLED(act, value):
  """called when an incoming remote activation occurs"""
  print("LED data recieved from:" + act.topic)
  myhw.setLED(act.unique, value)

  # act has a helper method useful for decoding boolean flags
  if act.isTrue(value):
    print("It's ON!")

#If no unique, raw name is used as-is, no callback prints data
dummy = IOT.reveal("dummy")

#If no callback, IOT module just prints incoming data
dummy1 = IOT.reveal("dummy", unique=1)
  
#multiple actuators can share the same callback
myLED  = IOT.reveal("led", incoming=changeMyLED) # no unique
myLED1 = IOT.reveal("led", incoming=changeMyLED, unique=1)
myLED2 = IOT.reveal("led", incoming=changeMyLED, unique=2)


# SUBSCRIBE TO REMOTE ACTUATION ----------------------------------------

theirLED = IOT.attachTo("them", "led")

# an unique can be used to disambiguate multiple instances of same thing
theirLED2 = IOT.attachTo("them", "led", unique=2)

# Unsubscribe from actuation

theirLED.forget()



# PUBLISH FEED ---------------------------------------------------------

# create a variable that is a feed you can publish data to
myButton = IOT.advertise("button")

# The unique can be used to disambiguate several instances of same thing
myButton2 = IOT.advertise("button", unique=2)


# SUBSCRIBE TO SOMEONE ELSE'S FEED -------------------------------------


#callback is called when new data arrives from the feed
def theirButtonChanged(feed, value):
  """Called when a remote feed publishes new data"""
  print("their button[" + str(feed.unique) + "] new value:" + str(value))
  # who is it from?
  # Note, I wanted to use ".from" here, but it's a Python keyword
  print("it came from:" + str(feed.originator))

#no callback causes the IOT library to just print incoming data
dummyButton = IOT.listenTo("them", "dummy")

#callback is called when data comes in from remote feed
theirButton = IOT.listenTo("them", "button", incoming=theirButtonChanged)

#sharing a callback is simple with unique
theirButton2 = IOT.listenTo("them", "button", unique=2, incoming=theirButtonChanged)


# Unsubscribe from a feed
dummyButton.forget()


# MAIN PROGRAM ---------------------------------------------------------

def main():
  state = False

  while True:
    time.sleep(1)
    
    # REMOTELY ACTUATE
    # a request without data (probably toggles/counts)
    theirLED.poke()
    
    # a request, with data (but might not be actioned)
    theirLED.ask(state)
    
    # a request with data (we get to hear if it fails/rejected)
    theirLED2.tell(state)
    
    state = not state
  
    # ADVERTISE A FEED
    b = myhw.checkButton(1)
    if b != None:
      myButton.share(b)
      myButton2.share(b)
    
try:
  main()
finally:
  IOT.cleanup()
  
# END
