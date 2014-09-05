# IoticLabs.JoinIOT - Join the Internet of Things
#
# This is an MQTT binding to the Iotic-labs connection broker.

import paho.mqtt.client as mqtt
import time
from Wait import WaitComplete
import os
import json
import sys, hashlib


# CONFIGURATION --------------------------------------------------------

DEFAULT_MYNAME = "Anon Geek"


def sortOfGetMacAddr():
  # If there are multiple interfaces, this will probably get a random
  # one (e.g. if eth0 and wlan0)
  import uuid
  m = uuid.getnode()
  return m


def getMacAddrStr():
  m = hex(sortOfGetMacAddr())
  # take off 0x
  m = m[2:]
  # take off L suffix
  if m[-1] == 'L':
    m = m[:-1]
  # left pad with zeros
  if len(m) < 12:
    req = 12 - len(m)
    m = ('0' * req) + m
  return m


def getEntityID():
  # Get Unique Entity ID for hash(machine + script) to enable testing multiple scripts on same device
  m = hashlib.md5()
  m.update(getMacAddrStr())
  m.update(sys.argv[0])
  return m.hexdigest()[:12].upper()


class IOTConfig:
  def __init__(self):
    # Hard coded defaults in case config_defaults.txt missing
    # These are used if key not set in config_defaults.txt
    self.MQTT_ID      = "davidw_" + str(os.getpid())
    self.CONTAINER_ID = "davidw"
    self.SERVER       = "demo.iotic-labs.com"
    self.MQTT_QOS     = 0
    self.MQTT_RETAIN  = False
    self.PORT         = 9210
    self.USER         = "davidw"
    self.PASSWORD     = "letmein"
    # TODO need to cache this on first use so it is always the same
    # and cache it in a file named based on the name of the
    # running script, in that directory if possible
    self.MY_ENTITY_ID = getEntityID()
    self.MY_NAME      = DEFAULT_MYNAME


  def read(self, name):
    """Read config from a file and overlay known keys"""
    print("warning:IOTConfig.read() UNIMPLEMENTED, using defaults in code")
    #read whole file into a map
    #iterate through all data members of this class
    #  if that key exists in file
    #    get type of member
    #    interpret value as that type and try to set it
    #close file when done

iotconfig = IOTConfig()



def trace(msg):
  print("IOT:" + str(msg))


# TOPIC-HELPERS --------------------------------------------------------

def makeTopic(entityId, *args):
  """Makes a topic name for use with our container"""
  n = iotconfig.CONTAINER_ID
  if entityId != None:
    n += "/" + entityId
  for i in args:
    n += "/" + i
  #print("makeTopic: returning '%s" % n)
  return n

# REGISTRATION

def makeRegisterTopic(entityId):
  #CID/LID/registerReq
  return makeTopic(entityId, "registerReq")


# FEEDS

def makePublishFeedTopic(entityId, feedId):
  #CID/LID/<feedid>/createFeedReq
  return makeTopic(entityId, feedId, "createFeedReq")

def makeFeedSubscribeTopic(entityId, feedId, guid):
  #CID/LID/GUID/<feedid>/subFeedReq
  #print("### " + str(entityId) + " " + str(feedId) + " " + str(guid))
  # This happens if you try to subscribe to a feed that does not exist
  if guid == None:
    raise ValueError("guid was None:" + str(entityId) + " " + str(feedId))

  return makeTopic(entityId, guid, feedId, "subFeedReq")

def makeFeedTopic(entityId, feedId):
  #CID/LID/<feedid>/feedSendReq
  return makeTopic(entityId, feedId, "feedSendReq")

def makeFeedAllTopic(entityId, feedId, guid):
  #CID/LID/GUID/<feedid>/#
  return makeTopic(entityId, guid, feedId, "#")


# ACTUATORS

def makePublishActuatorTopic(entityId, actId):
  #CID/LID/<actid>/createActReq
  return makeTopic(entityId, actId, "createActReq")

def makeActuatorSubscribeTopic(entityId, actId, guid):
  #CID/LID/GUID/<actid>/subActReq
  return makeTopic(entityId, guid, actId, "subActReq")

def makeActuatorDataRequestTopic(entityId, actId, guid):
  #from requester to requesters container, asking for remote actuation
  #CID/LID/GUID/<actid>/actSendReq
  return makeTopic(entityId, guid, actId, "actSendReq")

def makeActuatorAllTopic(entityId, actId, guid):
  #CID/LID/GUID/<actid>/#
  return makeTopic(entityId, guid, actId, "#")



# CALLBACK HELPER ------------------------------------------------------

class CallbackDispatcher(object):
  """Allows a topic to send callbacks to multiple destinations.
     This fixes a failing of the PAHO library, which only allows
     one callback registered per topic.
  """
  def __init__(self, client):
    self.client = client
    self.topics = {}

  def subscribe(self, topic, callback):
    trace("mux:subscribe:" + topic)
    if not self.topics.has_key(topic):
      #trace("mux:creating new callback record")
      # create a new callbacks entry with just our callback
      newCallbacks = [callback]
      # create a new local topic record for this topic
      self.topics[topic] = newCallbacks
      # register with paho client for callbacks on this topic
      client.message_callback_add(topic, self.handleIncoming)
    else:
      #trace("mux:appending to existing callback list")
      # append the new callback to this topic list
      self.topics[topic].append(callback)


  def handleIncoming(self, client, userdata, msg):
    topic = msg.topic
    trace("mux:incoming:" + topic)

    # first process any direct topic match
    if self.topics.has_key(topic):
      # there is a direct topic match
      cblist = self.topics[topic]
      #trace("there are " + str(len(cblist)) + " callbacks")
      for c in cblist:
        #trace("mux:calling callback")
        c(client, userdata, msg)
        #trace("mux:returned from callback")

    # now look for any "^*#$" wildcard entries, and dispatch if prefix matches
    for t in self.topics:
      if t[-1] == '#':
        # this is a wildcard topic
        #trace("mux:wildcard topic:" + t)
        #trace("compare:" + t + " and " + topic)
        if len(topic) >= len(t)-1:
          prefix = topic[:len(t)-1]
          #trace("mux:matching prefix:" + prefix)
          if prefix == t[:-1]:
            # the wildcard matches
            #trace("mux:wildcard match")
            cblist = self.topics[t]
            for c in cblist:
              #trace("mux:calling wildcard callback")
              c(client, userdata, msg)
              #trace("mux:returned from wildcard callback")


# HELPERS --------------------------------------------------------------

class Data(object):
  def __init__(self, topic, unique, originator=None):
    self.topic = topic
    self.unique = unique
    self.originator = originator

  """Useful utilities, passed forward with all FeedData and ActuatorData
  instances"""
  @staticmethod
  def isTrue(v):
    # How many different ways can you parse a boolean?
    # http://stackoverflow.com/questions/715417/converting-from-a-string-to-boolean-in-python
    if v == None:
      return False
    if type(v) == bool:
      return v
    if type(v) == str:
      if v.upper() in ['TRUE', 'T', 'YES', 'Y', '1']:
        return True
      else:
        return False
    if type(v) == int:
      return (v != 0)
    return False # give in, it must be False


# FEED -----------------------------------------------------------------

class FeedData(Data):
  def __init__(self, topic, unique=None, originator=None):
    Data.__init__(self, topic, unique, originator)


class Feed(object):
  def __init__(self, client, entityId, feedId):
    self.client     = client
    self.entityId   = entityId
    self.feedId     = feedId


class FeedProducer(Feed):
  """The local end of the feed, that produces data"""
  def share(self, value):
    #e.g. button1.share(True)

    w = WaitComplete()
    rspTopic = makeTopic(iotconfig.MY_ENTITY_ID, self.feedId, "feedSendRsp")
    client.message_callback_add(rspTopic, w.start())

    msg = json.dumps(value)
    topic = makeFeedTopic(iotconfig.MY_ENTITY_ID, self.feedId)
    #trace("publish:" + topic + "=" + msg)
    self.client.publish(topic, msg, iotconfig.MQTT_QOS, iotconfig.MQTT_RETAIN)

    trace("waiting for:" + rspTopic)
    if not w.wait():
      raise ValueError("Failed to publish feed data")
    trace("feed send OK")


class FeedConsumer(Feed):
  def __init__(self, client, entityId, feedId, incoming=None, userParams=None):
    Feed.__init__(self, client, entityId, feedId)
    self.userIncoming = incoming
    self.userParams   = userParams

  def handleIncoming(self, client, userdata, msg):
    """The remote end of the feed, that consumes data"""
    topic = msg.topic
    value = msg.payload

    trace("FeedConsumer.handleIncoming:" + topic + "=" + str(value))
    parts = topic.split('/')
    #CID/LID/guid/originator_lid/<feedId>/feed
    cmd = parts[-1]
    if cmd == "feed":
      # data path
      if (self.userIncoming != None):
        unique = None
        if self.userParams != None:
          if self.userParams.has_key('unique'):
            unique = self.userParams['unique']

        #TODO Pass userParams to constructor and let it fill in members
        fd = FeedData(topic, unique, parts[3])
        self.userIncoming(fd, value)
      else:
        trace("data path(unhandled):" + topic + "=" + str(value))
    else:
      # control path
      trace("control path(unhandled):" + topic + "=" + str(value))


# ACTUATOR -------------------------------------------------------------

class ActuatorData(Data):
  def __init__(self, topic, unique=None, originator=None):
    Data.__init__(self, topic, unique, originator)


class Actuator(object):
  def __init__(self, client, entityId, actId):
    self.client       = client
    self.entityId     = entityId
    self.actId        = actId
    self.guid         = None # lazy fetch


class ActuatorProducer(Actuator):
  """The remote end of an actuator that generates activiation reqs"""

  def poke(self):
    """Send a request, with no data"""
    self.send()

  def ask(self, data):
    """Send a request, with some data"""
    self.send(data)

  def tell(self, data, wait=False, completed=None, failed=None):
     """Send a command, with failure recovery"""
     #TODO, wait not implemented yet
     #TODO, completed not implemented yet
     #TODO, failed not implemented yet
     self.send(data)

  def send(self, value=None):
    """A low-level send of data to a remote actuator.
       You would not normally call this directly"""

    #e.g. led.send(True)
    #trace("send:" + self.entityId + "/" + self.actId + "=" + str(value))
    msg = json.dumps(value)
    if self.guid == None:
      self.guid = getGUID(self.entityId)
    topic = makeActuatorDataRequestTopic(iotconfig.MY_ENTITY_ID, self.actId, guid=self.guid)
    #trace("send:" + topic + "=" + msg)

    w = WaitComplete()
    rspTopic = makeTopic(iotconfig.MY_ENTITY_ID, self.guid, self.actId, "actSendRsp")
    client.message_callback_add(rspTopic, w.start())

    self.client.publish(topic, msg, iotconfig.MQTT_QOS, iotconfig.MQTT_RETAIN)

    trace("waiting for:" + rspTopic)
    if not w.wait():
      raise ValueError("Failed to actuate")
    trace("actuation OK")

    #TODO will have to handle Rsp callback to know if it is ok/failed


class ActuatorConsumer(Actuator):
  """The local end of an actuator that consumes remote act reqs"""

  def __init__(self, client, entityId, actId, incoming=None, userParams=None):
    Actuator.__init__(self, client, entityId, actId)
    self.userIncoming = incoming
    self.userParams   = userParams

  def handleIncomingAct(self, client, userdata, msg):
    trace("##incomingAct:" + msg.topic)
    #This is a placeholder to pass the "act" messages to.
    #not used at the moment

  def handleIncoming(self, client, userdata, msg):
    """The local end of an actuator that consumes remote actuations"""
    topic = msg.topic
    value = msg.payload

    trace("ActuatorConsumer.handleIncoming:" + topic + "=" + str(value))
    parts = topic.split('/')
    cmd = parts[-1]
    #trace("cmd:" + cmd)

    if cmd == "actSub":
      # subscription request
      trace("actSub:" + topic + "=" + str(value))
      if len(parts) != 5:
        trace("malformed actSub:" + topic)
        return

      guidOfRequester  = parts[2]
      actIdOfRequester = parts[3]
      if actIdOfRequester == self.actId:
        # subscription request to our actuator
        # subscribe to act feeds from it, to call our callback
        # CID/LID/GUID-of-subscriber/actId/act
        #actTopic = makeTopic(iotconfig.MY_ENTITY_ID, guidOfRequester, self.actId, "act")
        actTopic = makeTopic(iotconfig.MY_ENTITY_ID, "#")
        #trace("NOT subscribing to actuations from:" + actTopic)
        # Don't add a subscription inside a callback, it hangs paho/mqtt
        #to the point that it no longer processes messages
        #OLD WAYself.client.message_callback_add(actTopic, self.handleIncomingAct)
        #would use dispatcher anyway now
      else:
        trace("actId mismatch:" + actIdOfRequester + " " + self.actId)

    elif cmd == "act":
      # actuation data
      trace("act:" + topic + "+" + str(value))
      # must filter based on actId, as we get all acts
      #CID/LID/guid/originator_lid/<actId>/act
      if len(parts) != 6:
        trace("malformed actuation message:" + topic)
        return

      actId = parts[4]
      if actId != self.actId:
        # we receive all messages, so must filter here
        trace("actuation for someone else:" + actId)
        return

      # data path
      if (self.userIncoming != None):
        #pass in the kwargs passed into the constructor to disambiguate
        #things at the other end.
        # want feed.unique not feed['unique'] so have to create all
        #members programatically.
        #including feed.topic

        unique = None
        if self.userParams != None:
          #TODO use __setattr__ to set fields for all userParams?
          if self.userParams.has_key('unique'):
            unique = self.userParams['unique']
        #TODO pass user params to constructor and let it fill in members
        ad = ActuatorData(topic, unique, parts[3])
        self.userIncoming(ad, value)
      else:
        trace("incoming feed data(unhandled):" + topic + "=" + str(value))
    else:
      # control path
      trace("control path message(unhandled):" + cmd + " " + str(value))
      #TODO handle Rsp messages here


# KNITTING TO MQTT -----------------------------------------------------

#def on_message(client, userdata, msg):
#  trace("INCOMING:"+ msg.topic + "=" + str(msg.payload))
#  #dispatch(msg.topic, msg.payload)
#  #NOTE, this is replaced with per-object callbacks


# USER API -------------------------------------------------------------

##TODO use macAddr of node?
#what if more than one entity process on the node?
#user provides a user string as well
#perhaps entityId = macaddr+userstr
#If no user string, then all processes will get the same
#entityid on the same machine.
#could also do a dictionary generation of a name from the
#macaddr so that it at least looks like something sensible

client       = None # will be created by register()
dispatcher   = None # will be created and knitted by register()

def joinAs(myName, *args, **kwargs):
  join(myName=myName, *args, **kwargs)


def join(myName=None, meta=None, debug=False, silent=False,
  configName=None):
  """Register with the IOT"""
  global client, dispatcher, iotconfig

  if not debug:
    global trace
    def dummy(msg):
      pass
    trace = dummy

  trace("join")


  if configName == None:
    iotconfig = IOTConfig() # from hard coded defaults
    #TODO take care to get the path to this file
    #then basename it and add on config_defaults.txt
    #iotconfig.read("config_defaults.txt")
  else:
    iotconfig = IOTConfig()
    iotconfig.read(configName) #TODO not implemented yet

  if myName != None:
    # Override the name stored in the config
    iotconfig.MY_NAME = myName


  if meta == None:
    import NameToCoordinates as namer
    lat, lon = namer.getCoords(iotconfig.MY_NAME)
    if not silent:
      print("your name:" + iotconfig.MY_NAME)
      print("your coordinates:" + str(lat) + "," + str(lon))
    meta = {'type':'IOTIC-DEVICE', 'description':'THING', 'lat':lat, 'lon':lon}

  if not meta.has_key("name"):
    meta["name"] = iotconfig.MY_NAME



  # CONNECT
  trace("connecting")
  client = mqtt.Client(iotconfig.MQTT_ID)
  w = WaitComplete()

  if iotconfig.USER is not None:
    trace("using mqtt credentials %s / %s" % (iotconfig.USER, iotconfig.PASSWORD))
    client.username_pw_set(iotconfig.USER, iotconfig.PASSWORD)
  #client.on_message = on_message # FULL DEBUG
  client.on_connect = w.start()
  trace("calling connect")
  client.connect(iotconfig.SERVER, iotconfig.PORT, 60)
  trace("starting loop")
  client.loop_start()
  trace("waiting for response")
  if not w.wait():
    raise ValueError("could not connect")
  trace("connected")


  # SUBSCRIBE TO ALL TOPICS FOR OUR ENTITY
  client.subscribe(makeTopic(iotconfig.MY_ENTITY_ID, "#"))


  # REGISTER
  w = WaitComplete()
  topic = makeTopic(iotconfig.MY_ENTITY_ID, "registerRsp")
  client.message_callback_add(topic, w.start())

  msg = json.dumps(meta)
  trace("publishing registration request")
  client.publish(makeRegisterTopic(iotconfig.MY_ENTITY_ID), msg,
    iotconfig.MQTT_QOS, iotconfig.MQTT_RETAIN)

  trace("waiting for:" + topic)
  if not w.wait():
    raise ValueError("Failed to register")
  trace("registered OK")

  # set up a dispatcher for other classes to use
  dispatcher = CallbackDispatcher(client)

  if not silent:
    print("You are on the Internet of Things!")


def leave(permanent=False, wait=False, complete=None, failed=None):
  """Safe cleanup when program exits.
     use leave(permanent=True) if you want to de-register.
     use leave() when program exists for safe cleanup."""
  client.loop_stop()
  print("You are no longer on the Internet of Things")


# was publishFeed
def advertise(feedId, subscribe=None, meta=None, policy=None, complete=None,
  unique=None):
  """Advertise the availability of a feed"""
  trace("advertise")
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

  #tack on unique if it is used
  if unique != None:
    feedId += str(unique)

  w = WaitComplete()
  topic = makeTopic(iotconfig.MY_ENTITY_ID, feedId, "createFeedRsp")
  client.message_callback_add(topic, w.start())

  msg = json.dumps("")
  client.publish(makePublishFeedTopic(iotconfig.MY_ENTITY_ID, feedId), msg,
    iotconfig.MQTT_QOS, iotconfig.MQTT_RETAIN)

  trace("waiting for createFeedRsp")
  if not w.wait():
    raise ValueError("Failed to publish feed")
  trace("feed reg OK")

  return FeedProducer(client, iotconfig.MY_ENTITY_ID, feedId)


# was publishActuator
def reveal(actId, incoming=None, unique=None, meta=None, policy=None):
  """Reveal the availability of an actuator"""
  #TODO kwargs should be passed in the feed parameter to the callback

  trace("publishActuator")
  # (provide an actuator others can push to)
  # default if no meta is to use default meta
  # other parameters will be passed as part of the "actuator" collection
  # to the incoming handler so it can disambiguate requests
  #return an actuator local proxy
  #exception if cannot publish

  userParams = {}
  #If there is an unique, tack it onto the actuator ID to keep it unique
  if unique != None:
    actId += str(unique)
    userParams['unique'] = unique

  w = WaitComplete()
  topic = makeTopic(iotconfig.MY_ENTITY_ID, actId, "createActRsp")
  client.message_callback_add(topic, w.start())

  msg = json.dumps("")
  topic = makePublishActuatorTopic(iotconfig.MY_ENTITY_ID, actId)

  trace("  data topic:" + topic)
  client.publish(topic, msg, iotconfig.MQTT_QOS, iotconfig.MQTT_RETAIN)

  trace("waiting for createActRsp")
  if not w.wait():
    raise ValueError("Failed to publish actuator")
  trace("actuator reg OK")

  #TODO turn **kwargs into a map if not already one
  #m = **kwargs

  a = ActuatorConsumer(client, iotconfig.MY_ENTITY_ID, actId, incoming, userParams)

  # subscribe to the topic that causes this object to actuate
  #TODO cache it
  #myguid = getGUID(iotconfig.MY_ENTITY_ID)
  #topic = makeActuatorAllTopic(iotconfig.MY_ENTITY_ID, actId, myguid)
  topic = makeTopic(iotconfig.MY_ENTITY_ID, "#")
  trace("  all topic:" + topic)
  dispatcher.subscribe(topic, a.handleIncoming)
  #OLD WAYclient.message_callback_add(topic, a.handleIncoming)
  return a


# was subscribeFeed
def listenTo(entityId, feedId, incoming=None, complete=None, unique=None):
  """Subscribe to an already pubished feed"""
  #trace("subscribeFeed")
  # register for push notifications from another feed
  # given some known information about it
  # e.g. this data could come from a QRCode scan of the physical device
  #def marksButtonPressed(feed, value):
  #return a feed local proxy
  #exception if cannot subscribe

  #If the unique is used, tack it on to keep names unique
  if unique != None:
    feedId += str(unique)
  userParams = {'unique':unique}

  f = FeedConsumer(client, entityId, feedId, incoming, userParams)

  theirguid = getGUID(entityId)

  topic = makeFeedSubscribeTopic(iotconfig.MY_ENTITY_ID, feedId, theirguid)

  w = WaitComplete()
  rspTopic = makeTopic(iotconfig.MY_ENTITY_ID, theirguid, feedId, "subFeedRsp")
  client.message_callback_add(rspTopic, w.start())

  msg = json.dumps("")
  client.publish(topic, msg, iotconfig.MQTT_QOS, iotconfig.MQTT_RETAIN)

  trace("waiting for subFeedRsp")
  if not w.wait():
    raise ValueError("Feed subscription failed")
  trace("feed sub OK")

  # wire incoming feed to callback
  topic = makeTopic(iotconfig.MY_ENTITY_ID, "#")
  trace("  all topic:" + topic)
  dispatcher.subscribe(topic, f.handleIncoming)

  return f


# was subscribeActuator
def attachTo(entityId, actId, changed=None, complete=None,
  unique=None):
  """Subscribe to an already available actuator"""
  # eg
  #  # error if can't subscribe
  #  # returns local actuator proxy if it does subscribe
  #  #for led in found_leds:
  #  #  a = IOT.subscribeActuator(led):
  #  #  if a == None: (or exception)
  #  #    trace("sorry can't do that")
  #  #  else:
  #  #    myleds.append(a)
  #  #return an actuator local proxy

  #trace("subscribeActuator")
  #Subscribe to a specific actuation
  #return an actuator local proxy
  #exception if cannot subscribe

  # tack on the unique if it is used
  if unique != None:
    actId += str(unique)

  a = ActuatorProducer(client, entityId, actId)

  # make a topic that subscribes to the actuation request
  theirguid = getGUID(entityId)
  topic = makeActuatorSubscribeTopic(iotconfig.MY_ENTITY_ID, actId, guid=theirguid)
  trace("using topic:" + topic)

  w = WaitComplete()
  rspTopic = makeTopic(iotconfig.MY_ENTITY_ID, theirguid, actId, "subActRsp")
  client.message_callback_add(rspTopic, w.start())

  # publish to that topic
  msg = json.dumps("")
  client.publish(topic, msg, iotconfig.MQTT_QOS, iotconfig.MQTT_RETAIN)

  trace("waiting for subActRsp")
  if not w.wait():
    raise ValueError("Actuator subscription failed")
  trace("actuator sub OK")

  #there is no ActuatorProducer.incoming() - yet.
  #we might need a control channel for subscription updates.
  # subscribe to the topic that comes from this feed
  #topic = makeActuatorAllTopic(iotconfig.MY_ENTITY_ID, actId)
  #OLD WAYclient.message_callback_add(topic, a.handleIncoming)
  return a


#TODO also a feed.unsubscribe() and actuator.unsubscribe()???
#does this belong here?
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



# READ REGISTRAR DATABASE OF ENTITIES ----------------------------------
#TODO create a separate object to handle the transaction?
# This is a very dirty hack as it uses busy waiting,
# but it's enough for now. It reads the database once and
# keeps it cached, updating it only if the user asks for that.

registrar_database = None

def reqRegistrarDatabase():
  """asynchronously request registrar data"""
  # send listEntitiesReq
  topic = makeTopic(iotconfig.MY_ENTITY_ID, "listEntitiesRsp")
  client.message_callback_add(topic, rspRegistrarDatabase)
  msg = json.dumps("")
  client.publish(makeTopic(iotconfig.MY_ENTITY_ID, "listEntitiesReq"), msg,
    iotconfig.MQTT_QOS, iotconfig.MQTT_RETAIN)

def rspRegistrarDatabase(client, userdata, msg):
  """Handle the response from the registrar database"""
  global registrar_database
  #print("reg database rsp:" + str(msg.payload))
  registrar_database = json.loads(msg.payload)
  #print("reg database:" + str(registrar_database))
  #TODO probably pre-parse and build a local GUID database here
  #to make GUID lookups faster

def updateRegistrarDatabase():
  """Request the local registrar database cache to be updated"""
  #HACK - use callback
  global registrar_database
  registrar_database = None
  #trace("REQUESTING")
  reqRegistrarDatabase()
  while registrar_database == None:
    time.sleep(.1)
  #trace("GOTIT")

def getGUID(entityId, update=False):
  """Get the GUID for a given entityId, or name"""
  if registrar_database == None or update:
    updateRegistrarDatabase()

  print("looking for entity:" + entityId)
  for guid,data in registrar_database['entities'].iteritems():
    #print("guid:" + str(guid))
    #print("data:" + str(data))
    lid = data['lid']
    if data.has_key('meta'):
      meta = data['meta']
      metaj = json.loads(meta)
      if metaj.has_key('name'):
        name = metaj['name']
        if name == entityId:
          return guid
    print("entityId:" + lid)
    if lid == entityId:
      return guid
  raise ValueError("Can't find:" + str(entityId))


def search(wait=True, complete=None, failed=None, **kwargs):
  """Search for other things"""
  raise ValueError("Not yet implemented")


def startDiscovery(newAdvert=None, newReveal=None, **kwargs):
  """Start a background discovery process"""
  raise ValueError("Not yet implemented")


def stopDiscovery(identity):
  """Stop an existing background discovery process"""
  raise ValueError("Not yet implemented")


#IDEAS for .spec specifications (as files or kwparams or both)
#  # tempsensors.spec is all temperature sensors within 50 mile radius
#  # kwparams are unique to the spec, all optional
#  # if there is no spec provided, what is the default?
#  # returns a list of unsubscribed but subscribable matching feeds
#  #found_temps = IOT.findFeeds(spec="tempsensors.spec", radius=50)
#  #for feed in found_temps:
#  #  IOT.subscribeFeed(feed, incoming=handleTemperature)
#  # return an interator of feeds matching spec
#  return None # TODO return an iterator of feeds

#  # leds.spec is all leds I can turn on in a 50 mile radius
#  # radius is a %radius% parameter in the leds.spec file
#  # returns iterator of found subscribable actuators
#  # found_leds = IOT.findActuators(spec="leds.spec", radius=50)
#  # return an iterator of actuators matching spec
#  return None # TODO return an iterator of actuators


def loop(silent=False):
  """If you have nothing else to do (e.g. your system is entirely
  event driven) this is a useful loop"""
  try:
    count = 0
    while True:
      time.sleep(1)
      count += 1
      if not silent:
        print("tick:" + str(count))
  finally:
    if not silent:
      print("loop terminated")

# END


