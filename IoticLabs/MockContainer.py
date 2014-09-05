# MockContainer.py  05/08/2014  D.J.Whale
#
# A very simple container that just responds positively
# to all messages

import mosquitto as mqtt
import time


# CONFIGURATION --------------------------------------------------------
CONTAINER_ID = "wg"
PORT = 1883
SERVER = "localhost"
#SERVER = "test.mosquitto.org"
#SERVER = "iot.eclipse.org"

def trace(msg):
  print("MockContainer:" + str(msg))

registry = {}
  
  
# KNITTING TO MQTT -----------------------------------------------------

def on_connect(client, rc):
  trace("Connected with result code "+str(rc))
  #client.subscribe("$SYS/#")
  client.subscribe(CONTAINER_ID + "/#")
  
def on_message(client, msg):
  #trace(msg.topic + "=" + str(msg.payload))
  incoming(msg.topic, msg.payload)
  
client = mqtt.Mosquitto(CONTAINER_ID)
client.on_connect = on_connect
client.on_message = on_message
client.connect(SERVER, PORT, 60)



# INCOMING MESSAGE DISPATCH --------------------------------------------
def incoming(topic, value):
  #trace("incoming:" + topic + "=" + str(value))
  parts = topic.split("/")
  cmd = parts[-1]
  args = parts[0:-1]
  #trace("command:" + cmd)
  
  if cmd == "registerReq":
    registerReq(args, value)  
  elif cmd == "createFeedReq":
    createFeedReq(args, value)
  elif cmd == "createActReq":
    createActReq(args, value)
  elif cmd == "feedSendReq":
    feedSendReq(args, value)   
  elif cmd == "actSendReq":
    actSendReq(args, value)
  elif cmd == "listEntitiesReq":
    listEntities(args, value)
  else:
    unhandled(cmd, args, value)

def unhandled(cmd, args, value):
  trace("unhandled:" + cmd + " " + str(args))
  
def registerReq(args, value):
  #  rx: CID/LID/registerReq
  #  tx: CID/LID/registerRsp
  #trace("registerReq:" + str(args))
  #trace("  value:" + str(value))
  if len(args) != 2:
    trace("ERROR: malformed registerReq")
  else:
    cid, lid = args
    trace("REGISTER: localid:" + lid)
    if not registry.has_key(lid):
      registry[lid] = {"feeds":[], "acts":[]}

    topic = cid + "/" + lid + "/registerRsp"
    msg   = "{value:True}"
    client.publish(topic, msg, 0, True) #qos=0, retain=y
      
  
def createFeedReq(args, value):
  #  rx: CID/LID/<feedid>/createFeedReq
  #  tx: CID/LID/<feedid>/createFeedRsp
  #trace("createFeedReq:" + str(args))
  #trace("  value:" + str(value))
  if len(args) != 3:
    trace("ERROR: malformed createFeedReq")
  else:
    cid, lid, feedId = args
    trace("CREATE FEED:" + lid + " " + feedId)
    f = registry[lid]['feeds']
    f.append(feedId)

    topic = cid + "/" + lid + "/" + feedId + "/createFeedRsp"
    msg   = "{value:True}"
    client.publish(topic, msg, 0, True) #qos=0, retain=y
  
def createActReq(args, value):
  #  rx: CID/LID/<actid>/createActReq
  #  tx: CID/LID/<actid>/createActRsp
  #trace("createActReq:" + str(args))
  #trace("  value:" + str(value))
  if len(args) != 3:
    trace("ERROR: malformed createActReq")
  else:
    cid, lid, actId = args
    trace("CREATE ACT:" + lid + " " + actId)
    a = registry[lid]['acts']
    a.append(actId)

    topic = cid + "/" + lid + "/" + actId + "/createActRsp"
    msg   = "{value:True}"
    client.publish(topic, msg, 0, True) #qos=0, retain=y
  
def feedSendReq(args, value):
  #  rx: CID/LID/<feedid>/feedSendReq
  #  tx: CID/LID/<feedid>/feedSendRsp
  trace("feedSendReq:" + str(args))
  trace("  value:" + str(value))
  #NODO:incoming feed data, not to container?
  
def actSendReq(args, value):
  #  rx: CID/LID/GUID/<actid>/actSendReq
  #  tx: CID/LID/GUID/<actid>/actSendRsp  
  trace("actSendReq:" + str(args))
  trace("  value:" + str(value))
  #NODO:incoming actuation data, not to container?
  
def listEntities(args, value):
  #  rx: CID/LID/listEntitiesReq  
  #  tx: CID/LID/listEntitiesRsp 
  trace("listEntities:" + str(args))
  #trace("  value:" + str(value))
  #TODO:send back registry map in json format


# TOP LOOP
while client.loop() == 0:
  #msg = time.ctime()
  #client.publish("/whaleygeek/time", msg, 0, True) #qos=0, retain=y
  #print "time published"
  time.sleep(1)

# END

