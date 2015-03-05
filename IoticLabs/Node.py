# IoticLabs/Node.py  21/11/2014  D.J.Whale
#
# Manage a Node within a virtual space
# This is a factory method, to make the import process very simple
# i.e.:
#   import IoticLabs.Node

from VirtualSpace import Node

PRODUCER = Node.PRODUCER
CONSUMER = Node.CONSUMER

# Multi-noded implementation -------------------------------------------
# Use this if you want to create multiple nodes in a single application

def create(ownerName, nodeName, *args, **kwargs):
	"""Create a new Node"""
	return Node.create(nodeName, ownerName=ownerName, *args, **kwargs)

# Single-noded, non object oriented implementation ---------------------
# Use this interface with kids
	
theNode = None

def trace(msg):
	print(str(msg))
		
def node(ownerName, nodeName, *args, **kwargs):
	global theNode
	#trace("IOT.node")
	n = Node.create(nodeName, ownerName=ownerName, *args, **kwargs)
	theNode = n
	return n
	
def createProducer(pointName):
	#trace("IOT.createProducer")
	return theNode.createProducer(pointName)
	
def createConsumer(pointName, poke=None, ask=None, tell=None):
	#trace("IOT.createConsumer")
	return theNode.createConsumer(pointName, poke, ask, tell)
	
def find(forType, ownerName, nodeName, pointName):
	#trace("IOT.find")
	return theNode.find(forType, ownerName, nodeName, pointName)

def search(forType, *args, **kwargs):
	#trace("IOT.search")
	return theNode.search(forType, *args, **kwargs)

def discover(forType, wildcard="*", found=None, lost=None, *args, **kwargs):
	#trace("IOT.discover")
	theNode.discover(forType, wildcard, found, lost, *args, **kwargs)
		
def loop():
	#trace("IOT.loop")
	theNode.loop()
	
def sleep():
	#trace("IOT.sleep")
	theNode.sleep()
	

# END
