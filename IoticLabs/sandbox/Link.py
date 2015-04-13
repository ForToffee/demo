# Link.py  04/11/2014  D.J.Whale
#
# A generic link object that provides transport between two endpoints
# Part of the sandbox package.

import io
from Address import StrAddress
from DB import IdDatabase
import netcast  # netcast.Sender and netcast.Receiver
import time
import Multicast


# CONFIGURATION --------------------------------------------------------

# Note, this should be the only place this default test value is set.
DEFAULT_MULTICAST_ADDRESS = Multicast.DEFAULT_ADDRESS
DEFAULT_MULTICAST_PORT    = Multicast.DEFAULT_PORT
DEFAULT_LINKADDR          = Multicast.DEFAULT_LINKADDR


#DEPRECATED, but tester still uses it
META_FILE = "meta.txt"
DATA_FILE = "data.txt"


def trace(msg):
	print(str(msg))

def warning(msg):
	print("warning:" + str(msg))


# CONNECTION -----------------------------------------------------------

class Connection:
	def __init__(self, name):
		trace("new Connection")
		self.name = name

	def write(self, data):
		trace("write:" + str(data))

	def read(self, *args, **kwargs):
		trace("read")
		return None

	def close(self):
		trace("close")


# CODEC ----------------------------------------------------------------
# Code and decode message payloads

# Uses a string encoding of messages sent on the wire.
# Eventually we will support different encodings.

#TODO eventually call this a Codec() and put the coding and decoding
#of message payloads into a single class.

def parse(line):
	"""parse a line into msg, src, dest, data"""
	#trace("parse:" + line)

	# message (? ? ?) (? ? ?) data
	parts = line.split(" ", 1)
	# Get message
	msg = parts[0]
	if len(parts) == 1:
		# only a message, this is allowed
		return msg, None, None, None
	parts = parts[1]

	# Get src address
	try:
		lb = parts.index('(')
		rb = parts.index(')')
	except ValueError:
		trace("warning: No src address in line:" + str(line))
		return None # No valid message found
	src = parts[lb:rb + 1]

	# Get dst address
	parts = parts[rb + 2:]
	try:
		lb = parts.index('(')
		rb = parts.index(')')
	except ValueError:
		trace("warning: No dst address in line:" + str(line))
		return None # No valid message found
	dst = parts[lb:rb + 1]

	# Get optional data
	data = parts[rb + 2:]

	return msg, StrAddress.createFrom(src), StrAddress.createFrom(dst), data


# really should be:
# match(wanted(msg, src, dst), got(msg, src, dst))
# would be nice of these address classes also had a match() for complex wildcards
# like "anything like this, but not this one" so we can filter out our own address.

def match(wanted, gotMsg, gotSrc, gotDst):
	#trace("match:" + str(wanted) + " " + str(gotMsg) + " " + str(gotSrc) + " " + str(gotDst))

	# Check message filter
	wmsg = wanted.msg
	if wmsg != None and wmsg == "*":
		wmsg = None

	if wmsg != None and gotMsg != wmsg:
		#trace("message did not match")
		return False

	# Check src filter
	wsrc = wanted.src
	if wsrc != None and not StrAddress.match(wsrc, gotSrc):  # TODO check order
		#trace("src address did not match")
		return False

	# Check dst filter
	wdst = wanted.dst
	if wdst != None and not StrAddress.match(wdst, gotDst):  # TODO check order
		#trace("dst address did not match")
		return False
	#trace("MATCH")
	return True


# DISPATCHER -----------------------------------------------------------

class Info():
	def __init__(self, msg, src, dst):
		self.msg = msg
		self.src = src
		self.dst = dst

	def __repr__(self):
		return "Info(" + str(self.msg) + " " + str(self.src) + " " + str(self.dst) + ")"


class Dispatcher():
	# strategies for duplicate registration detection
	SQUASH = 0
	ACCEPT = 1
	ERROR  = 2

	def __init__(self):
		#trace("NEW DISPATCHER")
		self.listeners = []

	def registerListener(self, msg, src, dst, handler, duplicate=ERROR):
		#trace("Dispatcher.registerListener:" + str(msg) + " " + str(src) + " " + str(dst) + " " + str(handler))
		class Listener():
			def __init__(self, parent, msg, src, dst, handler):
				#trace("Listener.init")
				self.parent = parent
				self.msg = msg
				self.src = src
				self.dst = dst
				self.handler = handler

			def __repr__(self):
				return "Listener(" + str(self.msg) + " " + str(self.src) + " " + str(self.dst) + ") -> " + str(handler)

			def dispatch(self, msg, src, dst, data):
				#trace("Listener.dispatch")
				info = Info(msg, src, dst)
				#trace("dispatching:" + str(info) + " " + str(data))
				#trace("calling handler:" + str(handler))
				if handler == None:
					trace("warning, None handler for:" + str(info) + " " + str(data))
				else:
					self.handler(info, data)

			def unregister(self):
				trace("Listener.unregister")
				self.parent.unregister(self)

		# There are different strategies for duplicate registrations
		if duplicate == Dispatcher.ERROR:
			if self.isAlreadyRegistered(msg, src, dst, handler):
				raise ValueError(
					"Duplicate registration detected:" + str(msg) + " " + str(src) + " " + str(dst) + " " + str(
					handler))

		elif duplicate == Dispatcher.SQUASH:
			if self.isAlreadyRegistered(msg, src, dst, handler):
				#trace("squashed duplicate registration")
				return

		# ACCEPT, or SQUASH/ERROR without a duplicate
		#trace("Dispatcher.registerListener: msg=" + str(msg)
		#	+ " src=" + str(src) + " dst=" + str(dst) + " handler=" + str(handler))
		l = Listener(self, msg, src, dst, handler)
		self.listeners.append(l)
		return l


	def isAlreadyRegistered(self, msg, src, dst, handler):
		"""scan self.listeners for an existing record that matches"""
		for l in self.listeners:
			if l.msg == msg and str(l.src) == str(src) and str(l.dst) == str(dst) and str(l.handler) == str(handler):
				return True # already registered
		return False # not already registered


	def unregisterListener(self, l):
		#trace("FileConnectionPoller.unregisterListener TODO")
		# search for l through listeners
		# remove it from the list
		pass

	def multicast(self, msg, src, dst, data):
		"""Decide if this message needs dispatching"""
		#trace(" multicast:" + msg + " " + str(src) + " " + str(dst))

		#trace(" listeners:" + str(len(self.listeners)))
		for listener in self.listeners:
			#trace("  checking listener:" + str(listener))
			#trace("  against:" + str(msg) + " " + str(src) + " " + str(dst))
			if match(listener, msg, src, dst):
				#trace("  MATCH")
				self.dispatch(listener, msg, src, dst, data)

	def dispatch(self, listener, msg, src, dst, data):
		#trace("dispatch")
		# could add to a queue here, and process later
		listener.dispatch(msg, src, dst, data)


	def getConfig(self, indent=0):
		c = ""
		spc = " " * indent
		for listener in self.listeners:
			c += spc + str(listener) + "\n"
		return c


# CONNECTION POLLER -----------------------------------------------		

class ConnectionPoller():
	"""Polls a link looking for messages, and dispatches to handlers"""

	def __init__(self, link, debug=False):
		#trace("CP.NEW POLLER")
		self.link = link
		self.debug = debug
		self.dispatcher = Dispatcher()

	def registerListener(self, msg, src, dst, handler, duplicate=None):
		#trace("CP.registerListener")
		self.dispatcher.registerListener(msg, src, dst, handler, duplicate)

	def loop(self, maxtimes=10):
		"""Poll the data link for any incoming data"""

		count = 0
		while count < maxtimes:
			if self.link.isMessageWaiting():
				line = self.link.read()
				line = line.strip()
				parts = parse(line)
				if parts == None:
					trace("warning: Malformed packet:" + str(line))
				else:
					msg, src, dst, data = parts
					if self.debug:
						trace("ConnectionPoller:multicast try " + str(count) + ":" + str(msg)
							  + " " + str(src) + " " + str(dst) + " " + str(data))
					self.dispatcher.multicast(msg, src, dst, data)
					count += 1
			else:
				return  # bail if nothing to do


# FILE CONNECTION ------------------------------------------------------
# Note, when sharing between multi processes, might have to close file
# and reopen it every time, otherwise multi writer sync will not work.
# Might also need file locking, so that only one writer can write
# at any one time.

class FileConnection(Connection):
	def __init__(self, name):
		# open in read and write mode
		self.name = name
		self.f = io.open(name, "ab+")
		self.rpos = 0
		#self.wpos = 0
		self.moveToEnd()

	def write(self, data, *args, **kwargs):
		#trace("write:" + str(data))
		self.f.seek(0, io.SEEK_END)
		self.f.write(data + "\n")

	def isMessageWaiting(self):
		size = self.getSize()
		return (size > self.rpos)

	def getNextMessage(self):
		return self.blockingRead()

	def read(self, complete=None, *args, **kwargs):
		if complete == None:
			return self.blockingRead(*args, **kwargs)
		else:
			return self.nonBlockingRead(complete=complete, *args, **kwargs)

	def getSize(self):
		"""Get the present size of the open file"""
		self.f.seek(0, io.SEEK_END)
		size = self.f.tell()
		return size

	def moveToEnd(self):
		self.f.seek(0, io.SEEK_END)
		self.rpos = self.f.tell()
		return self.rpos

	def getPos(self):
		"""Get the position we have read up to"""
		return self.rpos

	def blockingRead(self, *args, **kwargs):
		#trace("blockingRead")
		self.f.seek(self.rpos, io.SEEK_SET)
		line = self.f.readline()
		self.rpos = self.f.tell()
		return line

	def nonBlockingRead(self, complete, *args, **kwargs):
		trace("nonBlockingRead")
		# claim busy mutex, only one nonBlockingRead per process
		# configure the thread read criteria
		# remember callback
		# kick off thread to do reading
		# thread will call callback when the read criteria matches.
		# thread will also clear the busy mutex for us
		trace("TODO: NOT YET WRITTEN")
		return None

	def close(self, *args, **kwargs):
		trace("close")
		self.f.close()
		self.f = None

	#def reopen(self):
	#	self.f = io.open(name, "a+")


# MulticastNetConnection ---------------------------------------------------
#
# This is a bit harder, because messages will come in via the multcast
# receiver, and we'll have to put them somewhere, perhaps in a queue
# for processing. The OS will have a small queue but this will overflow
# eventually, so really we need to have a regular poll of the netcast
# receiver (non blocking) that reads messages and adds to a local
# queue for later processing (perhaps in undecoded form?)

class MulticastNetConnection(Connection):

	@staticmethod
	def getAddress(linkPath):
		addr, port = linkPath.split(":", 1)
		return addr

	@staticmethod
	def getPort(linkPath):
		addr, port = linkPath.split(":", 1)
		return int(port)

	def __init__(self, address=None, port=None, name="Unknown"):
		if address == None:
			address = DEFAULT_MULTICAST_ADDRESS
		if port == None:
			port = DEFAULT_MULTICAST_PORT
		self.address = address
		self.port = port
		self.sender = netcast.Sender(address, port, name=name)
		self.receiver = netcast.Receiver(address, port, name=name)
		self.seq = 0
		self.receivers = {}

	def isMessageWaiting(self):
		return self.receiver.peek()

	def getNextMessage(self):
		return self._read()

	def write(self, data, *args, **kwargs):
		self.seq += 1
		payload = str(self.seq) + ":" + str(data)
		#trace("write:" + payload)
		self.sender.send(payload)

	def read(self, complete=None, *args, **kwargs):
		if complete == None:
			return self.blockingRead(*args, **kwargs)
		else:
			return self.nonBlockingRead(complete=complete, *args, **kwargs)

	def blockingRead(self, *args, **kwargs):
		#trace("MulticastNetConnection.blockingRead")
		return self._read()

	def nonBlockingRead(self, complete, *args, **kwargs):
		#trace("MulticastNetConnection.nonBlockingRead")
		return self._read()

	def _read(self):
		data, addr = self.receiver.receive()
		#trace("read:" + data)
		seq, payload = data.split(":", 1)
		self.check(addr, seq, payload)
		return payload

	def check(self, addr, seq, payload):
		if not self.receivers.has_key(addr):
			#trace("new receiver:" + str(addr))
			self.receivers[addr] = int(seq)  # starting seq no
		else:
			# check if seq no is correct
			seq = int(seq)
			expected_seq = (self.receivers[addr]) + 1
			if seq != expected_seq:
				warning("Unexpected seq addr:" + str(addr)
					  + " wanted:" + str(expected_seq) + " got:" + str(seq))
			#else:
			#	trace("ok: " + str(expected_seq) + " " + str(seq) + " " + str(payload))
			# resync on every msg
			self.receivers[addr] = seq

	def close(self, *args, **kwargs):
		#trace("MulticastNetConnection.close")
		self.sender.finished()
		self.sender = None
		self.receiver.finished()
		self.receiver = None


# META -----------------------------------------------------------------
# we can implement different policies, like:
#   is it a distributed registry (cached locally)?
#   is it a nominated registry?
#   is it an authoritative registry?
#   is it a voted registry?

#perhaps this local one is a cache updated every time something
#broadcasts a join/leave but when you join, you won't have a registry 
#at all and have to re-discover it.

#another way to do it is for a node to take on role of registry.

#another way is for a search to broadcast it's criteria, and anything
#that matches responds. Timeout/limit will cap responses.


# TODO because this has a link and a poller, it might mean that
# there can only be one of them? Although the poller will register
# with a dispatcher.

class Meta():
	@staticmethod
	def dbExists(dbPath):
		return IdDatabase.exists(dbPath)

	@staticmethod
	def getOwnerNames(dbPath):
		"""Get a list of owner names in dbPath database"""
		idb = IdDatabase(dbPath)
		idb.open()
		ownerNames = idb.getOwnerNames()
		idb.close()
		return ownerNames

	@staticmethod
	def getExistingDatabaseId(dbPath):
		"""Get the id of an existing database, by opening it and reading the DATABASE rec"""
		idb = IdDatabase(dbPath)
		idb.open()
		databaseId = idb.getDatabaseId()
		idb.close()
		return databaseId

	@staticmethod
	def createDatabase(dbPath, databaseId):
		if dbPath == None:
			raise ValueError("must provide a dbPath")
		if databaseId == None:
			raise ValueError("must provide a databaseId")

		IdDatabase.create(dbPath, databaseId)


	def __init__(self, link, databaseId, dbPath=None):
		self.link = link
		self.poller = ConnectionPoller(link)

		self.databaseId = databaseId
		self.addr = StrAddress(databaseId=databaseId)

		self.idb = IdDatabase(dbPath)
		self.idb.open()

		anyAddr = StrAddress.EMPTY

		self.poller.registerListener(None, anyAddr, anyAddr, self.handleMeta)


	# DATABASE SYNC ----------------------------------------------------
	# Must watch all meta messages on the link
	# to keep the distributed id database up to date

	def whoisOwner(self, ownerName):
		#trace("whoisOwner:" + str(ownerName))
		src = StrAddress(self.addr.ownerId, databaseId=self.databaseId)
		dst = StrAddress.EMPTY
		self.link.write("meta.whois.req " + str(src) + " " + str(dst) + " " + str(ownerName))


	def whoisNode(self, ownerId, nodeName):
		#trace("whoisNode:" + str(ownerId) + " " + str(nodeName))
		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		src = StrAddress(self.addr.ownerId, self.addr.nodeId, databaseId=self.databaseId)
		dst = StrAddress(ownerId)
		self.link.write("meta.whois.req " + str(src) + " " + str(dst) + " " + str(nodeName))


	def iAmNode(self, ownerId, databaseId, nodeId, nodeName, dst):
		#trace("iAmNode:" + str(ownerId) + " " + str(databaseId) + " " + str(nodeId) + " " + str(nodeName) + " => " + str(dst))
		src = StrAddress(ownerId, nodeId, databaseId=databaseId)
		self.link.write("meta.whois.rsp " + str(src) + " " + str(dst) + " " + nodeName)


	def whoisPoint(self, ownerId, databaseId, nodeId, pointName):
		#trace("whoisPoint:" + str(ownerId) + " " + str(nodeId) + " " + str(pointName))
		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		src = StrAddress(self.addr.ownerId, self.addr.nodeId, databaseId=self.databaseId)
		dst = StrAddress(ownerId, nodeId, databaseId=databaseId)
		self.link.write("meta.whois.req " + str(src) + " " + str(dst) + " " + str(pointName))


	def iAmPoint(self, ownerId, databaseId, nodeId, pointId, pointName, dst):
		#trace("iAmPoint:" + str(ownerId) + " " + str(databaseId) + " " + str(nodeId) + " " + str(pointId) + " " + str(pointName) + " => " + str(dst))
		src = StrAddress(ownerId, nodeId, pointId, databaseId=databaseId)
		self.link.write("meta.whois.rsp " + str(src) + " " + str(dst) + " " + pointName)


	def handleMeta(self, info, data):
		#trace("Meta.handleMeta:" + str(info) + " " + str(data))
		msg = info.msg
		src = info.src
		dst = info.dst

		# if it's from our own node, ignore it, as we already know!
		#TODO: This filtering should be done in the DISPATCHER, NOT HERE
		# TODO: if the dst address is us, we should process it anyway.
		# all we should squash is our own broadcasts.

		# IGNORE MY OWNER BROADCASTS (unless directed at me)
		#TODO: why is login not from a node?? signup should be only one!
		if src.nodeId == None:
			# just an owner message
			if src.ownerId != None and str(src.ownerId) == str(self.addr.ownerId):
				# we ignore broadcasts from ourself
				if dst.ownerId != None and str(dst.ownerId) != str(self.addr.ownerId):
					# but allow any that are directed at ourself
					#trace("DROP owner message from myself and not to myself:" + str(info) + " " + str(data))
					return

		# IGNORE MY NODE BROADCASTS (unless directed at me)
		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		if src.ownerId != None and str(src.ownerId) == str(self.addr.ownerId) \
				and src.nodeId != None and str(src.nodeId) == str(self.addr.nodeId):
			# a node message from ourself
			####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
			if src.nodeId != None and str(dst.nodeId) != str(self.addr.nodeId):
				# but allow any that are directed at ourself
				#trace("DROP node message from myself and not to myself:" + str(info) + " " + str(data))
				return

		# ignore misdirected messages that are not meta. messages
		if not msg.startswith("meta."):
			#TODO add wildcarding earlier??
			#trace("Ignoring non meta message:" + msg)
			return

		#trace("Meta.handleMeta:" + msg)

		if msg == "meta.signup.req":
			self.syncSignup(src, data)
		elif msg == "meta.create.req":
			self.syncCreate(src, data)

		elif msg == "meta.createpoint.req":
			#first word of data is type of point
			pointType, name = data.split(" ", 1)
			#trace("DB.pointType is" + pointType)
			#trace("name:" + name)
			self.syncCreatePoint(pointType, src, name)

		elif msg == "meta.advertise.req":
			self.syncAdvertise(src)
		elif msg == "meta.hide.req":  #TODO unadvertise
			self.syncHide(src)
		elif msg == "meta.bind.req":
			self.syncBind(src, dst, data)
		elif msg == "meta.bind.cnf":
			self.syncBindConfirm(src, dst, data)
		elif msg == "meta.bind.ind":
			self.syncBindIndication(src, dst, data)
		elif msg == "meta.unbind.req":
			self.syncUnbind(src, dst)
		elif msg == "meta.follow.req":  #TODO point specific
			self.syncFollow(src, dst)
		elif msg == "meta.unfollow.req":  #TODO point specific
			self.syncUnfollow(src, dst)
		elif msg == "meta.attach.req":  #TODO point specific
			self.syncAttach(src, dst)
		elif msg == "meta.release.req":  #TODO point specific
			self.syncRelease(src, dst)
		elif msg == "meta.state.ind":
			self.syncState(src, data)
		elif msg == "meta.login.req":
			pass  # nothing to do
		else:
			pass #trace("unhandled:" + str(info) + " " + str(data))


	def syncSignup(self, addr, ownerName):
		#trace("syncSignup:" + str(addr) + " " + str(ownerName))
		ownerId = addr.ownerId
		self.idb.rememberOwner(ownerName, ownerId=ownerId, databaseId=addr.databaseId)


	def syncCreate(self, addr, nodeName):
		#trace("syncCreate:" + str(addr) + " " + str(nodeName))
		ownerId    = addr.ownerId
		nodeId     = addr.nodeId
		databaseId = addr.databaseId
		self.idb.rememberNode(ownerId, nodeName, nodeId=nodeId, databaseId=databaseId)


	def syncCreatePoint(self, pointType, addr, name):
		#trace("syncCreatePoint:[" + str(addr) + "] [" + str(name) + "]")
		#TODO see if our id_database knows this name already
		#TODO add (addr) name to id_database as a POINT of type P
		ownerId    = addr.ownerId
		nodeId     = addr.nodeId
		pointId    = addr.pointId
		databaseId = addr.databaseId
		if self.idb.pointExists(ownerId, nodeId, pointType, name, databaseId):
			#trace("point already in database, ignoring:" + str(pointType) + " " + str(addr) + " " + name)
			return
		pointIdlocal = self.idb.rememberPoint(ownerId, nodeId, pointType, name, pointId, databaseId)
		return pointIdlocal


	def syncAdvertise(self, addr):
		#trace("syncAdvertise:" + str(addr))
		self.idb.advertise(addr.ownerId, addr.nodeId, addr.pointId, databaseId=addr.databaseId)

	def syncHide(self, addr):  #TODO: unadvertise
		self.idb.hide(addr.ownerId, addr.nodeId, addr.pointId)

	def syncBind(self, src, dst, data):
		#trace("syncBind:" + str(src) + " " + str(dst) + " " + str(data))
		pass

	# TODO this logic should be in Point.handleMeta???
	#syncronisation at the DB level should just keep the DB in step
	#but of course, the accept must be done by the Point()
	# perhaps a bind.cnf should be sent, that is picked up here
	# to keep the database up to date?

	def syncBindConfirm(self, src, dst, bindType):
		#trace("syncBindConfirm: src=" + str(src) + " dst=" + str(dst) + " bindType=" + str(bindType))
		self.idb.bind(bindType, src.ownerId, src.databaseId, src.nodeId, src.pointId,
					  dst.ownerId, dst.databaseId, dst.nodeId, dst.pointId)

	def syncBindIndication(self, src, dst, bindType):
		#trace("syncBindIndication: src=" + str(src) + " dst=" + str(dst) + " bindType=" + str(bindType))
		self.idb.bind(bindType, src.ownerId, src.databaseId, src.nodeId, src.pointId,
					  dst.ownerId, dst.databaseId, dst.nodeId, dst.pointId)


	def syncUnbind(self, src, dst):
		#trace("syncUnbind:" + str(src) + " " + str(dst))
		self.idb.unbind(src.ownerId, src.nodeId,
						dst.ownerId, dst.nodeId, dst.pointId)

	#def syncFollow(self, src, dst): #TODO this is point specific
	#	trace("deprecated syncFollow")
	#	#trace("syncFollow:" + str(src) + " " + str(dst))
	#	self.idb.follow(src.ownerId, src.nodeId,
	#		dst.ownerId, dst.nodeId, dst.pointId)

	#def syncUnfollow(self, src, dst): #TODO this is point specific
	#	trace("deprecated syncUnfollow")
	#	self.idb.unfollow(src.ownerId, src.nodeId,
	#		dst.ownerId, dst.nodeId, dst.pointId)

	#def syncAttach(self, src, dst): #TODO this is point specific
	#	trace("deprecated syncAttach")
	#	#trace("Meta.syncAttach:" + str(src) + " " + str(dst))
	#	self.idb.attach(src.ownerId, src.nodeId,
	#		dst.ownerId, dst.nodeId, dst.pointId)

	#def syncRelease(self, src, dst): #TODO this is point specific
	#	trace("deprecated syncRelease")
	#	self.idb.release(src.ownerId, src.nodeId,
	#		dst.ownerId, dst.nodeId, dst.pointId)

	def syncState(self, src, state):
		if state == "AWAKE":
			self.idb.wakeup(src.ownerId, src.nodeId)
		elif state == "ASLEEP":
			self.idb.sleep(src.ownerId, src.nodeId)
		else:
			pass #warning("unhandled state change:" + state)

	# ACCOUNT MANAGEMENT -----------------------------------------------

	def reset(self):
		"""Reset the Meta database to empty, mainly for testing"""
		self.idb.clear()

	def signup(self, ownerName, databaseId):
		"""signs up a new owner to the space"""
		self.addr.ownerId = self.idb.createOwner(ownerName)
		src = StrAddress(self.addr.ownerId, databaseId=databaseId)
		dst = StrAddress.EMPTY
		self.link.write("meta.signup.req " + str(src) + " " + str(dst) + " " + ownerName)
		return self.addr.ownerId

	def login(self, ownerName, databaseId):
		ownerId = self.idb.getOwnerId(ownerName)
		self.addr = StrAddress(ownerId, databaseId=databaseId)
		src = self.addr
		dst = StrAddress.EMPTY
		self.link.write("meta.login.req " + str(src) + " " + str(dst) + " " + ownerName)
		return self.addr.ownerId


	def getOwnerId(self, ownerName=None):
		"""Get owner id for name, or None if not known"""
		#trace("getOwnerId:" + str(ownerName))
		if ownerName == None:
			return self.addr.ownerId
		else:
			#trace("lookup")
			return self.idb.getOwnerId(ownerName)

	def getOwnerName(self, ownerId):
		return self.idb.getOwnerName(ownerId)

	def dissolve(self, ownerName):
		"""removes an owner account, like a company shutting down"""
		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		if self.addr.nodeId != None:
			raise ValueError("Can't dissolve, node still in use")
		ownerId = self.getOwnerId(ownerName)
		if ownerId != self.addr.ownerId:
			raise ValueError("Not owner, can't dissolve")
		self.addr.setNodeId(None)
		src = self.addr
		dst = StrAddress.EMPTY
		self.link.write("meta.dissolve.req " + str(src) + " " + str(dst))
		self.idb.deleteOwner(self.addr.ownerId)
		self.addr = None


	# NODE MANAGEMENT --------------------------------------------------

	def getNodeStateForName(self, ownerName, nodeName):
		# trace("Meta.getNodeState:" + str(ownerName) + " " + str(nodeName))
		ownerId = self.idb.getOwnerId(ownerName)
		if ownerId == None:
			return None

		nodeAddr = self.idb.getNodeAddr(ownerId, nodeName)
		if nodeAddr == None:
			return None

		databaseId = nodeAddr[0]
		nodeId     = nodeAddr[1]
		return self.getNodeStateForId(ownerId, nodeId, databaseId)


	def getNodeStateForId(self, ownerId, nodeId, databaseId):
		return self.idb.getNodeState(ownerId, nodeId, databaseId)


	def setNodeStateForId(self, ownerId, nodeId, state):
		#trace("Meta.setNodeState:" + str(ownerId) + " " + str(nodeId) + " " + str(state))
		self.idb.changeNodeState(ownerId, nodeId, state)
		src = StrAddress(ownerId, nodeId, databaseId=self.databaseId)
		dst = StrAddress.EMPTY
		self.link.write("meta.state.ind " + str(src) + " " + str(dst) + " " + state)


	def create(self, nodeName, nodeId=None):
		"""joins a new node to the space, creating an node in that space"""
		if self.addr.ownerId == None:
			raise ValueError("no ownerId set")
		nodeId = self.idb.createNode(self.addr.ownerId, nodeId, self.databaseId, nodeName)

		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		self.addr.nodeId = nodeId
		src = self.addr
		dst = StrAddress.EMPTY
		#should this only happen if it really creates it???
		self.link.write("meta.create.req " + str(src) + " " + str(dst) + " " + nodeName)
		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		return self.addr.nodeId


	def createNodeRef(self, ownerId, databaseId, nodeId, nodeName):
		"""Create a reference in db to someone else's node"""
		if ownerId == None:
			raise ValueError("Must supply an ownerId")
		if databaseId == None:
			raise ValueError("Must supply a databaseId")
		if nodeId == None:
			raise ValueError("Must supply a nodeId")
		if nodeName == None:
			raise ValueError("Must supply a nodeName")

		self.idb.createRemoteNode(ownerId, databaseId, nodeId, nodeName)


	def createPointRef(self, ownerId, databaseId, nodeId, pointId, pointName):
		"""Create a reference in db to someone else's node"""
		if ownerId == None:
			raise ValueError("Must supply an ownerId")
		if databaseId == None:
			raise ValueError("Must supply a databaseId")
		if nodeId == None:
			raise ValueError("Must supply a nodeId")
		if pointId == None:
			raise ValueError("Must supply a pointId")
		if pointName == None:
			raise ValueError("Must supply a pointName")

		self.idb.createRemotePoint(ownerId, databaseId, nodeId, pointId, pointName)


	def getNodeId(self, ownerId=None, nodeName=None):
		"""Get the id of the node this Meta object represents"""
		#trace("meta.getNodeId: ownerId:" + str(ownerId) + " nodeName:" + str(nodeName))
		if ownerId == None:  # use our ownerId
			if self.addr.ownerId == None:
				raise ValueError("my ownerId unexpectedly None")
			ownerId = self.addr.ownerId
		if nodeName == None:  # get our nodeId
			####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
			if self.addr.nodeId == None:
				raise ValueError("My nodeId unexpectedly None")
			####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
			return self.addr.nodeId
		else:
			#trace("looking up nodeId")
			return self.idb.getNodeId(ownerId, nodeName)


	def getNodeAddr(self, ownerId, nodeName):
		if ownerId == None:
			raise ValueError("Must provide an ownerId")
		if nodeName == None:
			raise ValueError("Must provide a nodeName")
		return self.idb.getNodeAddr(ownerId, nodeName)


	def getNodeName(self, ownerId, nodeId):
		return self.idb.getNodeName(ownerId, nodeId)


	def wakeup(self, ownerId, nodeId):
		"""rejoins an existing node to the space, waking up the avatar"""
		#trace("meta.wakeup")

		self.addr.set(ownerId, nodeId)
		src = self.addr
		dst = StrAddress.EMPTY
		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		self.idb.changeNodeState(self.addr.ownerId, self.addr.nodeId, "AWAKE")
		self.link.write("meta.wakeup.req " + str(src) + " " + str(dst))


	def sleep(self):
		"""temporary leave of a node, making the avatar sleep"""
		#TODO would be nice to check state to see if already asleep?
		src = self.addr
		dst = StrAddress.EMPTY
		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		self.idb.changeNodeState(self.addr.ownerId, self.addr.nodeId, "ASLEEP")
		self.link.write("meta.sleep.req " + str(src) + " " + str(dst))
		# This will prevent other services from working, intentionally
		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		self.addr.nodeId = None


	def delete(self, nodeName):
		"""permanent deletion of a node"""
		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		if self.addr.nodeId != None:
			raise ValueError("Can't delete node, it's still in use")
		nodeId = self.idb.getNodeId(self.addr.ownerId, nodeName)
		src = self.addr
		dst = StrAddress.EMPTY
		self.link.write("meta.delete.req " + str(src) + " " + str(dst))
		self.idb.deleteNode(self.addr.ownerId, nodeId)


	# POINT MANAGEMENT -------------------------------------------------

	####REORDER PARAMS
	def getPointId(self, ownerId, nodeId, pointName, databaseId):
		"""Get the id of the point for an owner and node"""
		if ownerId == None:  # use our ownerId
			ownerId = self.addr.ownerId
		if nodeId == None:  # get our nodeId
			####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
			nodeId = self.addr.nodeId

		return self.idb.getPointId(ownerId, nodeId, pointName, databaseId=databaseId)


	def getPointType(self, ownerId, nodeId, pointId, databaseId):
		return self.idb.getPointType(ownerId, nodeId, pointId, databaseId=databaseId)


	def createPoint(self, pointType, pointName):
		#trace("Meta.createPoint:" + str(pointType) + " " + str(pointName))

		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		pointId = self.idb.createPoint(self.addr.ownerId, self.addr.nodeId, pointType, pointName)
		src = StrAddress(self.addr.ownerId, self.addr.nodeId, pointId, databaseId=self.databaseId)
		dst = StrAddress.EMPTY
		self.link.write(
			"meta.createpoint.req " + str(src) + " " + str(dst) + " " + str(pointType) + " " + str(pointName))
		return pointId


	def advertise(self, pointId):
		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		src = StrAddress(self.addr.ownerId, self.addr.nodeId, pointId, databaseId=self.databaseId)
		dst = StrAddress.EMPTY
		self.idb.changePointState(self.addr.ownerId, self.addr.nodeId, pointId, "ADVERTISED")
		self.link.write("meta.advertise.req " + str(src) + " " + str(dst))
		#TODO: we don't change our idb.advertise here - why is this???
		#is this because we expect it to come back in via syncAdvertise??


	def hide(self, pointId):  #TODO unadvertise
		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		src = StrAddress(self.addr.ownerId, self.addr.nodeId, pointId, databaseId=self.databaseId)
		dst = StrAddress.EMPTY
		self.idb.changePointState(self.addr.ownerId, self.addr.nodeId, pointId, "HIDDEN")
		self.link.write("meta.hide.req " + str(src) + " " + str(dst))


	def remove(self, pointId):
		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		src = StrAddress(self.addr.ownerId, self.addr.nodeId, pointId, databaseId=self.databaseId)
		dst = StrAddress.EMPTY
		self.link.write("meta.remove.req " + str(src) + " " + str(dst))
		self.idb.deletePoint(self.addr.ownerId, self.addr.nodeId, pointId)


	#This is a general case of follow() and attach()
	def bind(self, bindType, ownerId, databaseId, nodeId, pointId):
		#return self.approvedBind(bindType, ownerId, databaseId, nodeId, pointId)
		return self.assumedBind(bindType, ownerId, databaseId, nodeId, pointId)


	def waitBind(self, bindType, ownerId, databaseId, nodeId, pointId):
		#trace("waiting for bind to succeed")
		src = self.addr
		dst = StrAddress(ownerId, nodeId, pointId, databaseId=databaseId)

		if bindType=="ONE_TO_MANY": # addresses must be swapped for follow
			src, dst = dst, src

		while True:
			self.loop() # allow message processing
			b = self.idb.isBound(src, dst, bindType)
			if b:
				return # bound
			#trace("WAIT for bind bindType:" + str(bindType) + " src:" + str(src) + " dst:" + str(dst))
			time.sleep(1)


	def assumedBind(self, bindType, ownerId, databaseId, nodeId, pointId):
		#trace("Meta.assumedBind: (" + str(ownerId) + " " + str(nodeId) + " " + str(pointId) + ")")
		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		src = StrAddress(self.addr.ownerId, self.addr.nodeId, databaseId=self.databaseId)
		dst = StrAddress(ownerId, nodeId, pointId, databaseId=databaseId)
		#trace("assumedBind: src=" + str(src) + " dst=" + str(dst))
		self.link.write("meta.bind.ind " + str(src) + " " + str(dst) + " " + str(bindType))
		# This is an assumed bind, so we write it directly to our database
		self.idb.bind(bindType, src.ownerId, src.databaseId, src.nodeId, src.pointId,
					  dst.ownerId, dst.databaseId, dst.nodeId, dst.pointId)

		#TODO inner class, should this be in VirtualSpace??
		class Binding():
			def __init__(self, meta, bindType, ownerId, nodeId, pointId):
				self.bindType = bindType
				self.ownerId = ownerId
				self.nodeId = nodeId
				self.pointId = pointId
				self.meta = meta

			def unbind(self):
				self.meta.unbind(self.ownerId, self.nodeId, self.pointId)

		return Binding(self, bindType, ownerId, nodeId, pointId)


	#TODO: This is a general case of follow() and attach()
	def approvedBind(self, bindType, ownerId, databaseId, nodeId, pointId):
		#trace("Meta.approvedBind:" + str(ownerId) + " " + str(nodeId) + " " + str(pointId))
		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		src = StrAddress(self.addr.ownerId, self.addr.nodeId, databaseId=self.databaseId)
		dst = StrAddress(ownerId, nodeId, pointId, databaseId=databaseId)
		# The other end of the binding makes the decision to allow/deny the bind.
		self.link.write("meta.bind.req " + str(src) + " " + str(dst) + " " + str(bindType))

		#TODO inner class, should this be in VirtualSpace??
		class Binding():
			def __init__(self, meta, bindType, ownerId, nodeId, pointId):
				self.bindType = bindType
				self.ownerId = ownerId
				self.nodeId = nodeId
				self.pointId = pointId
				self.meta = meta

			def unbind(self):
				self.meta.unbind(self.ownerId, self.nodeId, self.pointId)

		return Binding(self, bindType, ownerId, nodeId, pointId)

	def isBound(self, src, dst, bindType):
		return self.idb.isBound(src, dst, bindType)

	def bindConfirm(self, src, dst, bindType):
		self.link.write("meta.bind.cnf " + str(src) + " " + str(dst) + " " + str(bindType))

	def getBindingsFor(self, bindType, src=None, dst=None):
		return self.idb.getBindingsFor(bindType, src, dst)

	#TODO this is the general case of unfollow and release
	def unbind(self, ownerId, databaseId, nodeId, pointId):
		#trace("Meta.unbind")
		#TODO does this update some persistent record of local follows?
		#i.e. to allow them to be restored on reboot?
		####POSSIBLY DANGEROUS meta.addr.nodeId USAGE???
		src = StrAddress(self.addr.ownerId, self.addr.nodeId, pointId, databaseId=self.databaseId)
		dst = StrAddress(ownerId, nodeId, pointId, databaseId=databaseId)
		self.link.write("meta.unbind.req " + str(src) + " " + str(dst))


	def find(self, ownerName=None, nodeName=None, pointName=None, limit=1):
		"""find point by name, returns tuples:[(ownerId, nodeId, pointId)]"""
		#trace("meta.find ownerName:" + str(ownerName) + " nodeName:" + str(nodeName) + " pointName:" + str(pointName))
		#TODO need to consult global repository also eventually

		if ownerName == None:  # find a list of owners
			#trace("FIND OWNERS LIST")
			ownerIds = self.idb.getOwnerIds(limit=None)
			return ownerIds

		elif nodeName == None:  # find a list of nodes for an owner
			#trace("FIND NODE LIST FOR OWNER")
			ownerId    = self.idb.getOwnerId(ownerName)
			nodeAddrs  = self.idb.getNodeAddrs(ownerId, limit=None)
			return nodeAddrs

		elif pointName == None:  # find a list of points for a node
			#trace("FIND POINT LIST FOR NODE AND OWNER")
			ownerId = self.idb.getOwnerId(ownerName)
			nodeAddr = self.idb.getNodeAddr(ownerId, nodeName)
			databaseId = nodeAddr[0]
			nodeId     = nodeAddr[1]
			pointIds = self.idb.getPointIds(ownerId, nodeId, databaseId=databaseId, limit=None)
			return pointIds

		else:  # find a specific point name
			#trace("FIND POINT BY NAME")
			#trace("finding a point: ownerName:" + str(ownerName) + " nodeName:" + str(nodeName) + " pointName:" + str(pointName))
			ownerId    = self.idb.getOwnerId(ownerName)
			if ownerId == None:
				raise ValueError("Unknown owner:" + str(ownerName))
			nodeAddr   = self.idb.getNodeAddr(ownerId, nodeName)
			if nodeAddr == None:
				raise ValueError("Unknown node:" + str(nodeName))
			databaseId = nodeAddr[0]
			nodeId     = nodeAddr[1]
			pointId    = self.idb.getPointId(ownerId, nodeId, pointName, databaseId=databaseId)
			return pointId


	def search(self, forType):
		"""search for all points matching requirement"""
		raise ValueError("not yet implemented")
		#results = []
		#if (forType & PRODUCER) != 0:
		#	# find all producers
		#	for name in self.db:
		#		node = self.db[name]
		#		p = node["producers"]
		#		if len(p) > 0:
		#			results += p
		#
		#if (forType & CONSUMER) != 0:
		#	# find all consumers
		#	for name in self.db:
		#		node = self.db[name]
		#		c = node["consumers"]
		#		if len(c) > 0:
		#			results += c
		#TODO: block, waiting for right response
		#TODO: exception, or return
		#return results
		return None  # TODO


	def getNodeInfo(self, nodeId, databaseId):
		"""Get information about this node"""
		info = self.idb.getNodeRec(self.addr.ownerId, nodeId, databaseId=databaseId)
		return info


	def getPointRec(self, ownerId, nodeId, pointId, databaseId):
		#trace("getPointRec for:" + str(ownerId) + " " + str(nodeId) + " " + str(pointId))
		rec = self.idb.getPointRec(ownerId, nodeId, pointId, databaseId=databaseId)
		if rec == None:
			raise ValueError("No such point:" + str(ownerId) + " " + str(databaseId) + " " + str(nodeId) + " " + str(pointId))
		return rec


	def getPath(self, addr):
		"""Turn the numbered 'addr' into a string path"""
		#trace("meta.getpath: (" + str(addr))
		#This is a bit like turning an IP address into a DNS name
		r = "("
		if addr.ownerId != None:
			ownerName = self.idb.getOwnerName(addr.ownerId)
			r += ownerName
			if addr.nodeId != None:
				nodeName = self.idb.getNodeName(addr.ownerId, addr.nodeId, databaseId=addr.databaseId)
				r += "/" + nodeName
				if addr.pointId != None:
					pointName = self.idb.getPointName(addr.ownerId, addr.nodeId, addr.pointId, databaseId=addr.databaseId)
					r += "/" + pointName
		r += ")"
		return r


	#getPointRecs
	def getPoints(self, ownerId, nodeId):
		"""Get info records for all points for this nodeId"""
		#trace("Meta.getPoints")
		points = self.idb.getPointRecs(ownerId, nodeId, databaseId=self.addr.databaseId)
		return points


	#def getFollows(self, ownerId, nodeId, pointId):
	#	#trace("Meta.getFollows")
	#	follows = self.idb.getFollowRecs(ownerId, nodeId, pointId)
	#	return follows


	#def getAttachments(self, ownerId, nodeId, pointId):
	#	#trace("Meta.getAttachments")
	#	attachments = self.idb.getAttachmentRecs(ownerId, nodeId, pointId)
	#	return attachments


	def loop(self):
		"""Perform any regular message processing and housekeeping"""
		#trace("Meta.loop")
		self.poller.loop()


	def registerListener(self, msg, src, dst, handler, duplicate=None):
		#trace("Meta.registerListener for:" + str(msg) + " " + str(src) + " " + str(dst) + " " + str(handler))
		self.poller.registerListener(msg, src, dst, handler, duplicate)


	def unregisterListener(self, l):
		self.poller.unregisterListener(l)


	def getConfig(self, indent=0):
		return self.poller.dispatcher.getConfig(indent=indent)


# META TEST HARNESS ----------------------------------------------------

def testMeta():
	ownerName = "thinkingbinaries"
	nodeName = "sensor"
	pName = "temperature"
	cName = "catflap"

	m = Meta(link=FileConnection(META_FILE))
	m.reset()

	# SIGNUP
	ownerId = m.signup(ownerName)
	print("ownerId:" + str(ownerId))
	#ownerId = m.signup() # should fail
	#print("ownerId:" + str(ownerId))
	ownerId = m.getOwnerId(ownerName)
	print("ownerId:" + str(ownerId))


	# CREATE NODE
	nodeId = m.create(nodeName)
	print("nodeId:" + str(nodeId))
	#nodeId = m.create(nodeName) # should fail
	nodeId = m.getNodeId()
	print("nodeId:" + str(nodeId))


	# WAKEUP NODE (e.g. it's a login really, but it wakes up
	# the avatar
	m.wakeup(nodeName)
	m.wakeup(nodeName)  # should silently ignore, but still message
	nodeId = m.getNodeId()
	print("nodeId:" + str(nodeId))

	# CREATE PRODUCER
	#l_temperature = m.createProducer(pName)
	#print(m.idb.db.indexlist)
	#print(m.idb.db.indexmap)

	#l_catflap = m.createConsumer(cName)
	#print(m.idb.db.indexlist)
	#print(m.idb.db.indexmap)

	# ADVERTISE
	#TODO: do local advertisements have to be persisted somewhere???
	#i.e. so that we can restore them on reboot?
	#m.advertise(l_temperature)  # getPointId()
	#m.advertise(l_catflap)  # getPointId()

	# FOLLOW (self)
	#TODO: do local follows have to be persisted somewhere???
	#i.e. so that we can restore them on reboot?
	#f = m.follow(ownerId, nodeId, l_temperature)

	# ATTACH (self)
	#TODO: do local attachments have to be persisted somewhere???
	#i.e. so that we can restore them on reboot?
	#a = m.attach(ownerId, nodeId, l_catflap)

	# FIND - this is name related only
	# list of owners
	ids = m.find()
	print("all owners:" + str(ids))

	# list of nodes for an owner
	ids = m.find(ownerName)
	print("all nodes for:" + ownerName + " " + str(ids))

	# list of points for a node
	ids = m.find(ownerName, nodeName)
	print("all points for " + ownerName + "." + nodeName + " " + str(ids))

	# specific point name
	ids = m.find(ownerName, nodeName, pName)
	print("specific point:" + ownerName + "." + nodeName + "." + pName + " " + str(ids))


	# SEARCH - this looks at metadata about owners, nodes, points
	#ids = m.search(forType, criteria)
	#ids = m.search(forType, criteria)


	# UNFOLLOW
	#f.unfollow()
	#TODO:does this need to clear out a local persistent follow record?

	# RELEASE
	#a.release()
	#TODO:does this need to clear out a local persistent attachment record?


	# HIDE
	#m.hide(l_temperature)
	#m.hide(l_catflap)

	# REMOVE
	#m.remove(l_temperature)
	#m.remove(l_catflap)

	# SLEEP
	m.sleep()

	# DELETE this deletes a node, it's rare to use
	m.delete(nodeName)

	# DISSOLVE - the whole owner leaves
	# it's rare to use
	m.dissolve(ownerName)


# DATA -----------------------------------------------------------------

class Data():
	def __init__(self, ownerId, databaseId, nodeId, link):
		self.link = link
		self.poller = ConnectionPoller(link)
		self.addr = StrAddress(ownerId, nodeId, databaseId=databaseId)
		self.databaseId = databaseId


	def sendto(self, ownerId, databaseId, nodeId, pointId, data=None, fromPointId=None):
		#trace("Data.sendto: o=" + str(ownerId) + " d=" + str(databaseId) + " n=" + str(nodeId) + " p=" + str(pointId))
		src = StrAddress(self.addr.ownerId, self.addr.nodeId, fromPointId, databaseId=self.databaseId)
		dest = StrAddress(ownerId, nodeId, pointId, databaseId=databaseId)
		self.link.write("data.payload " + str(src) + " " + str(dest) + " " + str(data))


	def send(self, data=None, fromPointId=None):
		#trace("Data.send: fromPointId=" + str(fromPointId))
		src = StrAddress(self.addr.ownerId, self.addr.nodeId, fromPointId, databaseId=self.databaseId)
		dst = StrAddress()
		#trace("Data.send:" + str(src) + " " + str(dst))
		self.link.write("data.payload " + str(src) + " " + str(dst) + " " + str(data))


	def loop(self):
		"""Perform any regular message processing and housekeeping"""
		self.poller.loop()


	def registerListener(self, msg, src, dst, handler, duplicate=None):
		#trace("Data.registerListener:" + msg + " " + str(src) + " " + str(dst) + " " + str(handler))
		if handler == None:
			raise ValueError("attempt to register None handler")
		if src.nodeId != None and src.databaseId == None:
			raise ValueError("src node must be a global address")
		if dst.nodeId != None and dst.databaseId == None:
			raise ValueError("dst node must be a global address")

		self.poller.registerListener(msg, src, dst, handler, duplicate)


	def unregisterListener(self, l):
		self.poller.unregisterListener(l)


	def getConfig(self, indent=0):
		return self.poller.dispatcher.getConfig(indent=indent)

# END
