# MQTTTrace.py

import paho.mqtt.client as mqtt
import time
import os


# CONFIGURATION --------------------------------------------------------

MQTT_ID      = "whaleygeek_" + str(os.getpid())
CONTAINER_ID = "Team B"
#CONTAINER_ID = "whaleygeek"

PORT    = 1883
#SERVER  = "localhost"
#SERVER = "test.mosquitto.org"
#SERVER = "iot.eclipse.org"
SERVER = "54.77.126.143"

QOS = 0
RETAIN = False


def trace(msg):
  print("MQTTTrace:" + str(msg))
     

# KNITTING TO MQTT -----------------------------------------------------
  
def on_message(client, userdata, msg):
  trace("INCOMING:"+ msg.topic + "=" + str(msg.payload))
  #dispatch(msg.topic, msg.payload)
  #NOTE, this is replaced with per-object callbacks

def on_connect(client, userdata, msg):
  trace("CONNECTED")

# USER API -------------------------------------------------------------

MY_ENTITY_ID = None
client = None


def start(myEntityId):
  global MY_ENTITY_ID, client
  trace("register")
  MY_ENTITY_ID = myEntityId
  
  # CONNECT
  trace("connecting")
  client = mqtt.Client(MQTT_ID)
  
  client.on_message = on_message # FULL DEBUG
  client.on_connect = on_connect
  trace("calling connect")
  client.connect(SERVER, PORT, 60)
  trace("starting loop")
  client.loop_start()  
  
  # SUBSCRIBE TO ALL TOPICS FOR OUR ENTITY
  client.subscribe(CONTAINER_ID + "/" + MY_ENTITY_ID + "/#")
  
    
  
def cleanup(complete=None):
  """Safe cleanup at end"""
  client.loop_stop()

if __name__ == "__main__":
  #try:
  start("demo2")
  while True:
    print("tick")
    time.sleep(1)
  #except:
  #  cleanup()  

# END


