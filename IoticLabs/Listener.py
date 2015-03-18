# Listener.py  13/03/2015  D.J.Whale
#
# Low level listener interfaces for meta and data messages.
# This can be used to build sniffer based value added services in the sandbox.


from sandbox import Link
from Address import Address


def trace(msg):
	print(str(msg))


#TODO makeMeta and makeData might refactor into Link.py as factor methods?

def makeMeta(linkPath=None):
	if linkPath != None:
		address = Link.MulticastNetConnection.getAddress(linkPath)
		port    = Link.MulticastNetConnection.getPort(linkPath)
		meta_link = Link.MulticastNetConnection(name="VS.Owner", address=address, port=port)
	else:
		meta_link = Link.MulticastNetConnection(name="VS.Owner")

	return meta_link


def makeData(linkPath=None):
	if linkPath != None:
		address = Link.MulticastNetConnection.getAddress(linkPath)
		port    = Link.MulticastNetConnection.getPort(linkPath)
		data_link = Link.MulticastNetConnection(name="Listener.data", address=address, port=port)
	else:
		data_link = Link.MulticastNetConnection(name="Listener.data")

	return data_link


#TODO LinkListener, MetaListener and DataListener might refactor into Link.py
#They might be base classes for Meta and Data

class LinkListener():
	def __init__(self, linkPath=None):

		meta_link = makeMeta(linkPath)

		self.poller = Link.ConnectionPoller(meta_link)

		anyAddr = Address.EMPTY
		self.poller.registerListener(None, anyAddr, anyAddr, self.handleMsg)


	def __repr__(self):
		return "LinkListener(*)"


	def start(self):
		pass  # TODO reserved for threading


	def loop(self):
		"""Perform any regular message processing and housekeeping"""
		#trace("Meta.loop")
		self.poller.loop()


	def handleMsg(self, info, data):
		trace("handleMsg info=" + str(info) + " data=" + str(data))


class MetaListener(LinkListener):
	def __init__(self, linkPath = None):
		LinkListener.__init__(self, linkPath)


	def handleMsg(self, info, data):
		# FILTER
		if not info.msg.startswith("meta."):
			#trace("not a meta message:" + info.msg)
			return  # NOT HANDLED
		self.handleMeta(info, data)


	def handleMeta(self, info, data):
		# DECODE
		verb = info.msg[5:-4]  # Get the middle verb
		msgtype = info.msg[-3:] # last 3 always the type (req, rsp, ind, cnf)

		self.dispatch(verb, msgtype, info.src, info.dst, data)


	def dispatch(self, verb, msgtype, src, dst, data):
		#trace("meta: verb:" + str(verb) + " msgtype:" + str(msgtype) + " src:" + str(src) + " dst:" + str(dst))
		#trace("  " + str(data))

		#EXISTENCE
		#create       src=NodeAddr(o d.n), data=NodeLid
		if verb == "create":
			self.createNode(src, data)

		#createpoint  src=PointAddr(o d.n p), data=[GENERIC,FEED,CONTROL] PointLid
		elif verb == "createpoint":
			pointType, pointName = data.split(" ", 1)
			self.createPoint(src, pointType, pointName)

		#VISIBILITY
		#advertise    src=PointAddr(o d.n p)
		elif verb == "advertise":
			self.advertisePoint(src)

		#unadvertise  src=PointAddr(o d.n p)
		elif verb == "unadvertise":
			self.unadvertisePoint(src)

		#STATE
		elif verb == "state":
			#wakeup       src=NodeAddr(o d.n)
			if data == "AWAKE":
				self.wakeup(src)
			#sleep        src=NodeAddr(o d.n)
			elif data == "ASLEEP":
				self.sleep(src)
			else:
				trace("unhandled state change:" + str(data))

		#METADATA
		elif verb == "describe":
			#describe     src=NodeAddr(o d.n)     data=metadata
			if self.pointId == None: # it's a Node
				self.describeNode(src, data)
			else: # it's a Point
				#describe     src=PointAddr(o d.n p)  data=metadata
				self.describePoint(src, data)

		else:
			trace("meta:unhandled:" + " verb:" + str(verb) + " msgtype:" + str(msgtype) + " src:" + str(src) + " dst:" + str(dst))


	# OVERRIDE THIS INTERFACE
	def createNode(self, nodeAddr, name):
		trace("meta:createNode: addr:" + str(nodeAddr) + " name:" + str(name))


	def createPoint(self, pointAddr, pointType, name):
		trace("meta:createPoint: addr:" + str(pointAddr) + " type: " + str(pointType) + " name:" + str(name))


	def advertisePoint(self, pointAddr):
		trace("meta:advertisePoint: addr:" + str(pointAddr))


	def unadvertisePoint(self, pointAddr):
		trace("meta:unadvertisePoint: addr:" + str(pointAddr))


	def wakeup(self, nodeAddr):
		trace("meta:wakeup addr:" + str(nodeAddr))


	def sleep(self, nodeAddr):
		trace("meta:sleep addr:" + str(nodeAddr))


	def describeNode(self, nodeAddr, metadata):
		trace("meta:describeNode: addr:" + str(nodeAddr))
		trace("  " + str(metadata))


	def describePoint(self, pointAddr, metadata):
		trace("meta:describePoint: addr:" + str(pointAddr))
		trace("  " + str(metadata))



class DataListener(LinkListener):
	def __init__(self, linkPath = None):
		LinkListener.__init__(self, linkPath)


	def handleMsg(self, info, data):
		# FILTER
		if not info.msg.startswith("data."):
			#trace("not a meta message:" + info.msg)
			return  # NOT HANDLED
		self.handleData(info, data)


	def handleData(self, info, data):
		# DECODE
		#trace(str(info)) # "data.payload "
		channel, verb = info.msg.split(".", 1)

		self.dispatch(verb, info.src, info.dst, data)


	def dispatch(self, verb, src, dst, data):
		trace("data: verb:" + str(verb) + " src:" + str(src) + " dst:" + str(dst))
		trace("  " + str(data))


# TEST HARNESS

if __name__ == "__main__":
	import time
	linkPath = None # can be multicast-address:port

	ml = MetaListener(linkPath)
	dl = DataListener(linkPath)

	print("Listener test harness is running")
	while True:
		ml.loop()
		dl.loop()
		time.sleep(1)


# END
