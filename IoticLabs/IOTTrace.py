# arkessa.IOTTrace.py
#
# A simple tracing IOT interface.
# It's a sort of mock, but basically just tells you what it is doing.

#TODO we might need multiple instances of IOT as well, especially
#for local loopback testing where we might have two entities on
#the same machine or even in the same process talking to each other
#to test out the interfaces.

def trace(msg):
  print("arkessa.IOTTrace:" + str(msg))
  
  
# FEED -----------------------------------------------------------------

class Feed(object):
  def __init__(self, name):
    self.name = name
    
  def publish(self, value):
    trace("publish:" + self.name + "=" + str(value))
    #e.g. button1.publish(True)
  
class FeedProducer(Feed):
  """The local end of the feed, that produces data"""
  pass
  
class FeedConsumer(Feed):
  """The remote end of the feed, that consumes data"""
  pass
    
  

# ACTUATOR -------------------------------------------------------------

class Actuator(object):
  def __init__(self, name):
    self.name = name
    
  def actuate(self, value):
    trace("actuate:" + self.name + "=" + str(value))
    #e.g. led.actuate(True)
    
class ActuatorProducer(Actuator):
  """The remote end of an actuator that generates activiation reqs"""
  pass
  
class ActuatorConsumer(Actuator):
  """The local end of an actuator that consumes remote act reqs"""
  pass
  




#callback signatures for incoming subscripton requests
#note is there a higher layer "event" such as subscribe, unsubscribe
#etc, that has a default demultiplex to these functions? 
#callback def subscribeButton(feed, requester):
#callback def subscribeMyLED(actuator, requester):



def loop():
  trace("loop")
  #call this regularly in a thread to make it all happen.
  #TODO need a default thread that could be started to do this for us
  #pass
  #nothing to return

    
def register(name=None):
  trace("register")
  # First time round this creates a new entity, caches details.
  # Next time round just reuses existing entity from the cache.
  # we will never need to register more than one of these in a program

  # Assumes there are credentials required to identify owner of the entity
  # probably cached in credentials.txt as owner/public key
  # this name is also the destination for the push, so each instance
  # of a program must have a different name

  # default if you don't give a name, is to call it after the
  # mac address and the processid of the machine that this runs on
  #nothing to return
  #exception if cannot register


def publishFeed(feedName, subscribe=None, meta=None, policy=None):
  trace("publishFeed")
  # publish a new feed on my entity thing "button"
  # as described by "davidsbutton.meta"??

  # default if there is no meta parameter, is to use a default metadata
  # that just puts a string in {data=""}, configured by config file
  # default if no policy is to use a policy configured by config file?

  # optionally wire up subscription handler after feed has been created.
  # Any requests that come in before this point get the default
  # handler defined in the policy, which might be to accept anything
  # or accept up to a certain number.
  #return a feed local proxy
  #exception if cannot publish
  return FeedProducer(feedName)
  

def publishActuator(actuatorName, incoming=None, id=None, meta=None, policy=None):
  trace("publishActuator")
  # (provide an actuator others can push to)
  # default if no meta is to use default meta
  # other parameters will be passed as part of the "actuator" collection
  # to the incoming handler so it can disambiguate requests
  #return an actuator local proxy
  #exception if cannot publish
  return ActuatorConsumer(actuatorName)


def subscribeFeed(entityName, feedName, incoming):
  trace("subscribeFeed")
  # register for push notifications from another feed
  # given some known information about it
  # e.g. this data could come from a QRCode scan of the physical device
  #def marksButtonPressed(feed, value):
  #return a feed local proxy
  #exception if cannot subscribe
  return FeedConsumer(feedName)
  

#def subscribeFeed(entityName, feedId):
#  trace("subscribeFeed")
#  # error if can't subscribe
#  # returns local actuator proxy if it can subscribe
#  # a.actuate(value)  
#  #return a feed local proxy
  

def subscribeActuator(entityName, actuatorName, changed=None):
  trace("subscribeActuator")
  #Subscribe to a specific actuation  
  #return an actuator local proxy
  #exception if cannot subscribe
  return ActuatorProducer(actuatorName)
  
  
#def subscribeActuator(actuator):
#  trace("subscribeActuator")
#  # error if can't subscribe
#  # returns local actuator proxy if it does subscribe
#  #for led in found_leds:
#  #  a = IOT.subscribeActuator(led):
#  #  if a == None:
#  #    print("sorry can't do that")
#  #  else:
#  #    myleds.append(a)
#  #return an actuator local proxy
  

#TODO also a feed.unsubscribe() and actuator.unsubscribe()???
#TODO does this belong here?
#def unsubscribe(ref):
#  trace("unsubscribe")
#  # unsubscribe from a feed that we subscribe to
#  # unsubscribe from an actuator that we subscribe to
#  #nothing to return
#  #exception if cannot unsubscribe


#TODO force a remote end to unsubscribe from a feed
#this could also be a method of either end of a feed
#how would you identify which remote instance to unsubscribe?

#TODO force a remote end to unsubscribe from an actuation
#this could also be a method of either end of an actuator
#how would you identify which remote instance to unsubscribe?


#TODO SEARCH GUI in Tkinter
#This will be in another module "search"
# a search/discovery GUI lists identities and their entities
# choose an entity and put it into contacts list with alias name
# really this is an entity GUID behind the scenes
# presumably we can also connect to our own feeds too
# From this we found an entity called "mark_wharton" that has a
# feed called "button1".


def findFeeds(spec, **kwargs):
  trace("findFeeds")
  # tempsensors.spec is all temperature sensors within 50 mile radius
  # kwparams are unique to the spec, all optional
  # if there is no spec provided, what is the default?
  # returns a list of unsubscribed but subscribable matching feeds
  #found_temps = IOT.findFeeds(spec="tempsensors.spec", radius=50)
  #for feed in found_temps:
  #  IOT.subscribeFeed(feed, incoming=handleTemperature)
  # return an interator of feeds matching spec
  return None # TODO return an iterator of feeds


def findActuators(spec, **kwargs):
  trace("findActuators")
  # leds.spec is all leds I can turn on in a 50 mile radius
  # radius is a %radius% parameter in the leds.spec file
  # returns iterator of found subscribable actuators
  # found_leds = IOT.findActuators(spec="leds.spec", radius=50)
  # return an iterator of actuators matching spec
  return None # TODO return an iterator of actuators
  

#TODO register a discovery callback for feeds and actuators
#complete with a spec, new entities, new feeds, new actuators
#might be a separate helper class



# END


