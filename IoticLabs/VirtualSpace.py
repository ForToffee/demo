# VirtualSpace.py  03/11/2014  D.J.Whale

from Address import Address
from sandbox.Link import Dispatcher
import time
import Config as cfg


# CONFIGURATION --------------------------------------------------------

# Knit up to the underlying transport
# This should be the only thing to change when moving to new transport

import sandbox.Link as Link

#TODO: deprecate this
DEFAULT_DATABASE_NAME = "test"
DEFAULT_OWNER_NAME    = "tester"
#DEFAULT_NODE_NAME = "node" [instance]
#DEFAULT_POINT_NAME = "point" [instance]

WHOIS_POLL_RATE = cfg("whois.pollrate", default=5)


# This allows VirtualSpace.CONSUMER and VirtualSpace.PRODUCER
# if all you do is import VirtualSpace. But really they are types of
# Point and don't really belong here long term.
# They are duplicated in Link.py as it needs a verb to send over the
# wire - that's fine for now, at least they are linked.

def trace(msg):
	print(str(msg))

def warning(msg):
	print("warning:" + str(msg))



# SCAFFOLDING -----------------------------------------------------------------
# Temporary scaffolding
# Eventually this will have to get a globally unique ID
# For now, you could just type in the ID number on the front of a
# RaspberryPi SD card.

def getNewDatabaseId():
	"""Get the id of a new database to create"""
	try:
		databaseId = int(cfg("dbid"))
		return databaseId
	except KeyError:
		warning("Can't find dbid in config")

	print("please supply a globally unique number")
	while True:
		databaseId = raw_input("New databaseId:")
		try:
			databaseId = int(databaseId)
			return databaseId
		except ValueError:
			print("Must be a whole number")
		if databaseId <= 0:
			print("Must be greater than zero")


def getExistingDatabaseId(dbPath):
	"""Get the id of an existing database, by opening it and reading the DATABASE rec"""
	return Link.Meta.getExistingDatabaseId(dbPath)


def guessDatabaseName():
	"""Make an educated guess at the database name to use in this folder"""

	# First ask the config if a dbpath has been provided
	# as that overrides all other options.
	try:
		dbpath = cfg("dbpath", default=None)
		return dbpath
	except KeyError:
		warning("no dbpath in config, scanning directory instead")


	# get list of databases in current folder (files with name *.db)
	import glob
	candidateNames = glob.glob("*.db")
	if len(candidateNames) == 0:
		# No databases in folder
		return DEFAULT_DATABASE_NAME # use a sensible default

	elif len(candidateNames) == 1:
		return (candidateNames[0])[:-3] # use the only one, but strip extension

	else:
		# N databases in folder
		# Provide a list for the user to choose from
		i = 1
		print("CHOOSE A DATABASE")
		for n in candidateNames:
			print(str(i) + ". " + n)
			i += 1
		while True:
			choice = raw_input("Open which database?")
			try:
				choice = int(choice)
				if choice < 1 or choice > len(candidateNames):
					print("Must choose a number between 1 and " + str(len(candidateNames)))
				else:
					return (candidateNames[choice-1])[:-3] # strip extension
			except ValueError:
				print("Must choose a number")

# OWNER -----------------------------------------------------------------------

class Owner():
	default_owner = None
	#TODO: this is not multi-owner safe
	#Needs to be owner instance, not owner class
	#should be self.nodes{}
	all_nodes     = {} # nodeName->Node

	@staticmethod
	def use(ownerName=None, dbPath=None, linkPath=None):
		"""Use this ownerName as default, or guess one"""

		if dbPath == None:
			#trace("dbPath not provided, guessing")
			dbPath = guessDatabaseName()
			#trace("guessed it to be:" + str(dbPath))

		if not Link.Meta.dbExists(dbPath):
			# Create a new databaseId
			#trace("creating new databaseId")
			databaseId = getNewDatabaseId()
			#trace("creating new database with DATABASE rec")
			Link.Meta.createDatabase(dbPath, databaseId)
		else:
			# Use an existing database
			#trace("using existing databaseId from path:" + str(dbPath))
			databaseId = getExistingDatabaseId(dbPath)

		if ownerName == None:
			#trace("no ownerName provided, guessing from dbPath:" + str(dbPath))
			ownerName = Owner.guess(dbPath)

		o = Owner(ownerName, databaseId, dbPath=dbPath, linkPath=linkPath)

		if Owner.default_owner == None:
			#trace("This is the new default owner")
			Owner.default_owner = o

		return o


	@staticmethod
	def guess(dbPath):
		"""Guess an ownerName from any previous persisted context"""

		if dbPath == None:
			raise ValueError("Must provide a dbPath")

		# Database does exist, so ask it about OWNER names.
		ownerNames = Link.Meta.getOwnerNames(dbPath)
		if len(ownerNames) == 0:
			return DEFAULT_OWNER_NAME
		if len(ownerNames) == 1:
			return ownerNames[0]

		print("CHOOSE AN OWNER")
		i=1
		for o in ownerNames:
			print(str(i) + ". " + o)
			i += 1

		while True:
			choice = raw_input("choice?")
			try:
				choice = int(choice)
				if choice < 1 or choice > len(ownerNames):
					print("Must enter a number between 1 and " + str(len(ownerNames)))
				else:
					return ownerNames[choice-1]
			except ValueError:
				print("Must enter a number")

		# If there is only one owner name, use that
		# If there is more than one, offer a list, ask user to select


	def __init__(self, ownerName, databaseId, dbPath=None, linkPath=None):
		if databaseId == None:
			raise ValueError("Must provide a databaseId")
		if linkPath == None:
			linkPath = cfg("lanaddr", default=None)
		self.ownerName  = ownerName
		self.dbPath     = dbPath
		self.linkPath   = linkPath
		self.databaseId = databaseId

		#TODO: refactor as makeMeta() to be consistent with makeData()
		if linkPath != None:
			address = Link.MulticastNetConnection.getAddress(linkPath)
			port    = Link.MulticastNetConnection.getPort(linkPath)
			self.meta_link = Link.MulticastNetConnection(name="VS.Owner", address=address, port=port)
		else:
			self.meta_link = Link.MulticastNetConnection(name="VS.Owner")

		self.meta = Link.Meta(link=self.meta_link, dbPath=dbPath, databaseId=databaseId)


		ownerId = self.meta.getOwnerId(ownerName)
		if ownerId == None:
			#trace("SIGNUP")
			ownerId = self.meta.signup(ownerName, databaseId)
		else:
			#trace("LOGIN")
			ownerId = self.meta.login(ownerName, databaseId)
		#trace("ownerId:" + str(ownerId))
		if ownerId == None:
			raise ValueError("Owner not created")
		self.ownerId = ownerId
		anyAddr = Address.EMPTY
		#trace("Owner registers listener for handleMeta")
		#TODO could be more restrictive in registration
		#i.e. dst=(o), so that filtering is done earlier.
		self.meta.registerListener(None, anyAddr, anyAddr, self.handleMeta)


	def getStateForNode(self, nodeName, ownerName=None):
		if ownerName == None:
			ownerName = self.ownerName

		return self.meta.getNodeStateForName(ownerName, nodeName)


	def handleMeta(self, info, data):
		#trace("Owner.handleMeta:" + str(info) + " " + str(data))
		# FILTER
		if not info.msg.startswith("meta."):
			#trace("not a meta message:" + info.msg)
			return  # NOT HANDLED

		# we only process meta messages for this ownerId
		#trace("filter? us:(" + str(self.addr) + " sender:" + str(info))
		if info.dst.nodeId != None:
			return  # NOT HANDLED
		#trace("filter match Owner")

		# DECODE
		verb = info.msg[5:-4]  # Get the middle verb
		msgtype = info.msg[-3:] # last 3 always the type

		self.dispatch(verb, msgtype, info.src, data)

	def dispatch(self, verb, msgtype, src, data):
		#trace("Owner.dispatch: src=" + str(src) + " verb=" + str(verb) + " type=" + str(msgtype) + " data=" + str(data))

		if verb == "whois" and msgtype == "req":
			self.handleWhoisRequest(src, data)


	def handleWhoisRequest(self, src, nodeName):
		#trace("Owner.whois src=" + str(src) + " data=" + str(nodeName))
		if not self.all_nodes.has_key(nodeName):
			#trace("Node not managed here, ignoring:" + nodeName)
			return

		node = self.all_nodes[nodeName]
		#trace("found and delegating to node:" + str(node))
		node.sendWhoisResponse(src)


# NODE -----------------------------------------------------------------

class Node():
	# Node.STATE (INIT state
	CREATED  = "CREATED"
	BOUND    = "BOUND"
	RESTORED = "RESTORED"
	AWAKE    = "AWAKE"
	ASLEEP   = "ASLEEP"

	@staticmethod
	def create(nodeName, nodeId=None, owner=None):
		"""Factory method that creates a new Node"""
		# trace("Node.create()")
		if owner == None:
			owner = Owner.default_owner

		n = Node(owner)
		n._create(nodeName, nodeId)
		# trace("node meta:" + str(n.meta))
		#TODO: This is not multi-owner safe.
		# needs to be owner instance, not owner class.
		#should be self.nodes{}
		Owner.all_nodes[nodeName] = n
		return n


	@staticmethod
	def restore(nodeName, nodeId=None, owner=None):
		"""Factory method that restores a previous Node"""
		# trace("Node.restore:" + str(nodeName))
		if owner == None:
			owner = Owner.default_owner

		meta = owner.meta
		ownerId = owner.ownerId

		if nodeId != None:
			nodeId = str(nodeId)
		else:
			nodeId = meta.getNodeId(ownerId, nodeName)
			if nodeId == None:
				raise ValueError("Node does not exist:" + owner.ownerName + " " + nodeName)

		# trace("  restoring:" + str(ownerId) + " " + str(nodeId))

		# Use memoize pattern to restore existing in-memory copy if it exists
		nodeId = str(nodeId)
		ownerId = str(ownerId)
		#TODO: This is not multi owner safe
		#needs to be owner instance, not owner class
		#should be self.nodes{}

		for nodeName in Owner.all_nodes:
			#TODO: This is not multi owner safe
			#needs to be owner instance, not owner class
			#should be self.nodes{}
			n = Owner.all_nodes[nodeName]
			#trace("  node:" + str(n))
			#trace("  " + str(n.ownerId) + " " + str(n.nodeId))
			if str(n.owner.ownerId) == ownerId and str(n.nodeId) == nodeId:
				#trace("  restoring from memory:" + str(n))
				n.setState(Node.RESTORED)
				return n

		# If get here, it's not in memory from a previous create()
		# so we have to manually restore it from metadata
		#trace("  restoring from metadata")
		n = Node(owner)
		n._restore(nodeName)
		#trace("  node:" + str(n))
		n.setState(Node.RESTORED)
		#TODO: This is not multi owner safe
		#needs to be owner instance, not owner class
		#should be self.nodes{}
		Owner.all_nodes[nodeName] = n
		return n


	def __init__(self, owner):
		self.owner = owner
		self.nodeId = None

		#just a local cache for self.owner.meta
		self.meta = None

		self.points = {} # pointName->Point()
		self.loopUsed = False

		# Can't register meta listener until nodeId is known.


	def __repr__(self):
		return "Node(" + str(self.owner.ownerId) + " " + str(self.owner.databaseId) + "." + str(self.nodeId) + ")"


	def getState(self):
		# trace("getState:"+ str(self.owner.ownerId) + " " + str(self.nodeId))
		return self.meta.getNodeStateForId(self.owner.ownerId, self.nodeId)


	def setState(self, state):
		# trace("Node.setState:" + str(state))
		self.meta.setNodeStateForId(self.owner.ownerId, self.nodeId, state)

	def _makeData(self, databaseId):
		linkPath = self.owner.linkPath
		if linkPath != None:
			address = Link.MulticastNetConnection.getAddress(linkPath)
			port    = Link.MulticastNetConnection.getPort(linkPath)
			data_link = Link.MulticastNetConnection(name="VS.Node.data", address=address, port=port)
		else:
			data_link = Link.MulticastNetConnection(name="VS.Node.data")

		data = Link.Data(self.owner.ownerId, databaseId, self.nodeId, link=data_link)
		return data


	#TODO: DRY - lots of repeated code with _restore
	def _create(self, nodeName, nodeId=None):
		# trace("_create")

		# convenience cache
		self.meta = self.owner.meta
		self.nodeName = nodeName

		if nodeId != None:
			nodeId = str(nodeId)

		ownerId = self.meta.getOwnerId(self.owner.ownerName)
		if ownerId == None:
			raise ValueError("Owner has not been created")


		# CREATE NODE if not already created
		actualNodeId = self.meta.getNodeId(ownerId=None, nodeName=nodeName)

		if actualNodeId != None:
			raise ValueError("Node already exists")

		actualNodeId = self.meta.create(nodeName, nodeId)
		if actualNodeId == None:
			raise ValueError("node not created")

		self.nodeId = actualNodeId
		self.data = self._makeData(self.owner.databaseId)
		self.addr = Address(self.owner.ownerId, self.nodeId, databaseId=self.owner.databaseId)
		self.setState(Node.CREATED)

		#trace("Node registers listener for handleMeta")
		#TODO could be more restrictive in registration
		#i.e. dst=(o), so that filtering is done earlier.
		anyAddr = Address.EMPTY
		self.meta.registerListener(None, anyAddr, anyAddr, self.handleMeta)


	#TODO: DRY - lots of repeated code with _create
	def _restore(self, nodeName):
		# trace("_restore")

		# convenience cache
		self.meta = self.owner.meta
		self.nodeName = nodeName

		actualNodeId = self.meta.getNodeId(ownerId=None, nodeName=nodeName)
		if actualNodeId == None:
			raise ValueError("Unknown Node:" + str(nodeName))

		self.nodeId = actualNodeId
		self.data = self._makeData(self.owner.databaseId)
		self.addr = Address(self.owner.ownerId, self.nodeId, databaseId=self.owner.databaseId)

		#TODO do we need to change state here?

		#trace("Node registers listener for handleMeta")
		#TODO could be more restrictive in registration
		#i.e. dst=(o), so that filtering is done earlier.
		anyAddr = Address.EMPTY
		self.meta.registerListener(None, anyAddr, anyAddr, self.handleMeta)


	def handleMeta(self, info, data):
		#trace("# Node.handleMeta info=" + str(info) + " data=" + str(data))

		# FILTER
		if not info.msg.startswith("meta."):
			#trace("not a meta message:" + info.msg)
			return  # NOT HANDLED

		# we only process meta messages for a (o d.n) address
		if info.dst.ownerId == None or info.dst.databaseId == None or info.dst.nodeId == None \
			or info.dst.pointId != None:
			#trace("not a Node message")
			return  # NOT HANDLED

		#trace("myaddr: " + str(self.addr))
		#trace("dst:" + str(info.dst))
		if not Address.match(self.addr, info.dst):
			#trace("not for my Node")
			return  # NOT HANDLED

		#trace("matched for my node")


		# DECODE
		verb = info.msg[5:-4]  # Get the middle verb
		msgtype = info.msg[-3:] # last 3 always the type

		self.dispatch(verb, msgtype, info.src, info.dst, data)


	def dispatch(self, verb, msgtype, src, dst, data):
		#trace("# dispatch verb:" + str(verb) + " msgtype:" + str(msgtype))
		if verb == "whois" and msgtype == "req":
			self.handleWhoisRequest(src, data)

		if verb == "whois" and msgtype == "rsp":
			# careful here, we can receive both Node whois.rsp and Point whois.rsp
			if src.pointId == None:
				# This is a Node whois response
				nodeName = data
				self.handleNodeWhoisResponse(src, nodeName)
			else:
				# This is a Point whois response
				pointName = data
				self.handlePointWhoisResponse(src, pointName)


	def wakeup(self):
		# trace("Node.wakeup:" + str(self.owner.ownerId) + " " + str(self.nodeId))
		self.setState(Node.AWAKE)



	def start(self):
		pass  # TODO reserved for threading


	def loop(self):
		self.meta.loop()
		self.data.loop()
		self.loopUsed = True


	def createPoint(self, pointName, nodeId=None, pointType=None):
		"""one-time create of a local point of a specific type"""

		# trace("Node.createPoint:" + str(pointName))
		if pointType == None:
			pointType = Point.GENERIC
		if nodeId == None:
			nodeId = self.nodeId

		endType = Point.LOCAL  # always LOCAL
		p = Point.metaCreate(pointType, endType, self.owner.ownerId, self.owner.databaseId, nodeId, pointName,
							 meta=self.meta, pointId=None)
		self.points[pointName] = p
		return p


	def routePoint(self, endType, pointName, nodeName=None, receive=None):
		"""Find and route one of our bindings to appropriate callbacks"""

		#trace("Node.routePoint:" + str(self.owner.ownerName) + " " + str(nodeName) + " " + str(pointName))

		if nodeName == None: # default to my owner/node
			nodeAddr = (self.owner.databaseId, self.nodeId)
		else: # eventually might want to override owner, so this will have to change
			nodeAddr = self.meta.getNodeAddr(self.owner.ownerId, nodeName)
			if nodeAddr == None:
				raise ValueError("Unknown node:" + str(nodeName))

		# create the in-memory representation of the Point, LOCAL or REMOTE
		databaseId = nodeAddr[0]
		nodeId     = nodeAddr[1]
		pointId = self.meta.getPointId(self.owner.ownerId, nodeId, pointName, databaseId=databaseId)
		if pointId == None:
			raise ValueError("Unknown point:" + str(pointName)
							 + " owner:" + str(self.owner.ownerId) + " databaseId:" + str(databaseId) + " nodeId:"+ str(nodeId))

		rec = self.meta.getPointRec(self.owner.ownerId, nodeId, pointId, databaseId=databaseId)
		pointType = rec["pointType"]
		p = Point.metaRestore(pointType, endType, self.owner.ownerId, nodeId, pointName, pointId, meta=self.meta, data=self.data,
							  	databaseId=databaseId)

		# Route any updates to this Point() through to the user supplied receive function.
		p.setCallbacks(receive)
		p.numBindings = 0

		# Set up data routing, any messages for this pointId routed to this Point() instance
		# which ultimately goes to the user supplied receive function.

		if endType == Point.REMOTE:

			# receiving end of a follow:  REMOTE   ONE_TO_MANY   src(o d.n p)->dst()
			#trace("  REMOTE FOLLOW (receiving end of follow)")
			src = Address(self.addr.ownerId, nodeId, pointId, databaseId=databaseId)
			#trace("  src:" + str(src))

			bindings = self.meta.getBindingsFor(bindType=Point.ONE_TO_MANY, src=src)
			#trace("  bindings:" + str(bindings))
			for b in bindings:
				src = Address(b["srcOwnerId"], b["srcNodeId"], b["srcPointId"], databaseId=b["srcDatabaseId"])
				dst = Address(b["dstOwnerId"], b["dstNodeId"], databaseId=b["dstDatabaseId"])
				anyAddr = Address.EMPTY
				#trace("FOLLOW LISTENER " + str(src) + "=>" + str(dst))
				#trace("my addr:" + str(self.addr))
				if Address.match(self.addr, dst):
					#trace(" found my binding")
					####TODO, only if dst matches our address, should we register a callback
					#otherwise we'll get everyone else's registrations too!
					self.data.registerListener("data.payload", src, anyAddr, p.handleReceive)
					p.numBindings += 1
				else:
					pass#trace("warning: must be a binding for someone else - ignoring")

			# sending end of an attach: REMOTE MANY_TO_ONE src(o d.n)->dst(o d.n p)
			#trace("  REMOTE ATTACH (sending end of attach)")
			#dst = Address(self.addr.ownerId, self.addr.nodeId, pointId, databaseId=databaseId)
			#trace("  dst:" + str(dst))

			#bindings = self.meta.getBindingsFor(dst=dst, bindType=Point.MANY_TO_ONE)
			#trace("  bindings:" + str(bindings))

			#for b in bindings:
			#	src = Address(b["dstOwnerId"], b["dstNodeId"], b["dstPointId"], b["dstDatabaseId"])
			#	dst = Address.EMPTY # right for addressing, but wrong for bind table lookup, get too much back???
			#	#trace("attach sender " + str(src) + "=>" + str(dst))
			#	# no registrations to do, but would expect a binding
			#	p.numBindings += 1

			#if p.numBindings == 0:
			#	raise ValueError("No REMOTE bindings were found in DB for:" + pointName)

		elif endType == Point.LOCAL:

			# receiving end of an attach: LOCAL    MANY_TO_ONE   src(o d.n)->dst(o d.n p)
			#trace("  LOCAL ATTACH (receiving end of attach)")
			dst = Address(self.addr.ownerId, self.addr.nodeId, pointId, databaseId=databaseId)
			#trace("  dst:" + str(dst))

			bindings = self.meta.getBindingsFor(dst=dst, bindType=Point.MANY_TO_ONE)
			#trace("  bindings:" + str(bindings))

			for b in bindings:
				src = Address(b["srcOwnerId"], b["srcNodeId"], databaseId=b["srcDatabaseId"])
				dst = Address(b["dstOwnerId"], b["dstNodeId"], b["dstPointId"], databaseId=b["dstDatabaseId"])
				#trace("ATTACH LISTENER " + str(src) + "=>" + str(dst))
				self.data.registerListener("data.payload", src, dst, p.handleReceive)
				p.numBindings += 1


			# receiving end of an attach: LOCAL    MANY_TO_ONE   src(o d.n)->dst(o d.n p)
			#trace("  LOCAL FOLLOW (sending end of follow)")
			#src = Address(self.owner.ownerId, self.addr.nodeId, pointId, databaseId=self.owner.databaseId)
			#trace("  src:" + str(src))

			#bindings = self.meta.getBindingsFor(bindType=Point.ONE_TO_MANY, src=src)
			#trace("  bindings:" + str(bindings))

			#for b in bindings:
			#	src = Address(b["srcOwnerId"], b["srcNodeId"])
			#	dst = Address(b["dstOwnerId"], b["dstNodeId"], b["dstPointId"]) ####DATABASEID???
			#	#trace("FOLLOW SENDER " + str(src) + "=>" + str(dst))
			#	p.numBindings += 1

			#if p.numBindings == 0:
			#	trace("warning: no bindings found in DB for:" + pointName)

		else:
			trace("warning: endType was not known:" + str(endType))
			raise ValueError("Unknown endType")

		self.points[pointName] = p
		return p


	def handleWhoisRequest(self, dst, pointName):
		#trace("Node.handleWhoisRequest:" + str(dst) + " " + str(pointName))
		if self.points.has_key(pointName):
			#trace("my point, delegating")
			p = self.points[pointName]
			p.handleWhoisRequest(dst, pointName)
		else:
			#trace("# Not one of my points, ignoring")
			pass


	def sendWhoisResponse(self, dst):
		#trace("send WHOIS response for me:" + str(self) + " to them:" + str(dst))
		self.meta.iAmNode(self.owner.ownerId, self.owner.databaseId, self.nodeId, self.nodeName, dst)


	def handleNodeWhoisResponse(self, src, nodeName):
		#trace("Node.handleNodeWhoisResponse for me:" + str(self) + " from them:" + str(src) + " nodeName:" + str(nodeName))
		self.meta.createNodeRef(src.ownerId, src.databaseId, src.nodeId, nodeName)


	def handlePointWhoisResponse(self, src, pointName):
		#trace("Node.handlePointWhoisResponse for me:" + str(self) + " from them:" + str(src) + " pointName:" + str(pointName))
		self.meta.createPointRef(src.ownerId, src.databaseId, src.nodeId, src.pointId, pointName)


	def sleep(self):
		self.setState(Node.ASLEEP)


	def leave(self):
		raise ValueError("leave is DISABLED")



	def find(self, pointName, ownerName=None, nodeName=None, wait=True, timeout=None, pointType=None):
		"""Find a specific node and it's point"""
		#trace("Node.find:" + str(ownerName) + " " + str(nodeName) + " " + str(pointName))

		if pointType == None:
			pointType = Point.GENERIC
		if timeout == None:
			timeout = cfg("find.timeout", default=60)

		# Find a reference to the Owner
		if ownerName == None:
			ownerId = self.owner.ownerId
		else:
			ownerId = self.meta.getOwnerId(ownerName)
			if ownerId == None:
				raise ValueError("Owner not found:" + ownerName)
				#TODO insert whois poll pattern here

		# find a reference to the Node
		if nodeName == None:
			nodeAddr = (self.owner.databaseId, self.nodeId)
		else:
			nodeAddr = self.meta.getNodeAddr(ownerId, nodeName)
			if nodeAddr == None:
				if wait: # wait for node to be created
					trace("warning: waiting for node:" + nodeName)
					now = time.time()
					tout = now + timeout
					while now < tout:
						self.meta.whoisNode(ownerId, nodeName)
						self.loop()
						nodeAddr = self.meta.getNodeAddr(ownerId, nodeName)
						if nodeAddr != None:
							trace("found node:" + nodeName)
							break
						now = time.time()
						time.sleep(WHOIS_POLL_RATE) # poll rate to limit whois messaging

					if nodeAddr == None:
						raise ValueError("timeout waiting for Node:" + nodeName)
				else:
					raise ValueError("node not found:" + nodeName)

		# find a reference to the Point
		databaseId = nodeAddr[0]
		nodeId = nodeAddr[1]
		pointId = self.meta.getPointId(ownerId, nodeId, pointName, databaseId=databaseId)
		if pointId == None:
			if wait: # wait for node to be created
				trace("warning: waiting for point:" + pointName)
				now = time.time()
				tout = now + timeout
				while now < tout:
					self.meta.whoisPoint(ownerId, databaseId, nodeId, pointName)
					self.loop()
					pointId = self.meta.getPointId(ownerId, nodeId, pointName, databaseId=databaseId)
					if pointId != None:
						trace("found point:" + pointName)
						break
					now = time.time()
					time.sleep(WHOIS_POLL_RATE) # poll rate to limit whois messaging

				if pointId == None:
					raise ValueError("timeout waiting for point:" + pointName)
			else:
				raise ValueError("point not found:" + pointName)

		#TODO should really check that the point is ADVERTISED

		# create a proxy reference object to the remote Point
		pointType = self.meta.getPointType(ownerId, nodeId, pointId, databaseId=databaseId)
		endType = Point.REMOTE
		p = Point.metaRestore(pointType, endType, ownerId, nodeId, pointName, pointId, self.meta, self.data, databaseId=databaseId)
		return p



	##TODO should this be Point.search() @staticmethod
	# with a redirector here?
	#def search(self, forType, *args, **kwargs):
	#	raise ValueError("not yet implemented")

	# """blocking search for anything"""
	#
	#	#trace("S:search")
	#	return g_meta.search(forType)


	#TODO should this be Point.discover() @staticmethod
	#with a redirector here?
	#def discover(self, forType, wildcard="*", found=None, lost=None, *args, **kwargs):
	#	raise ValueError("Not yet implemented")

	#	"""non blocking background search for anything"""
	#	#this could just listen for join/leave messages, as it is only delta's?
	#	#or is it? would you need to do a search() to get what is there, and then
	#	#do a discover to find new ones? Or is discover like a long running search
	#	#that never ends?
	#	if found != None:
	#		#TODO run this in loop()
	#		#really need to just follow a data point from VirtualSpace
	#		#that tells us new advertisements
	#		results = search(forType, *args, **kwargs)
	#		for r in results:
	#			found(r)
	#
	#		#TODO what about lost() callback?
	#		#this would just follow a data point from VirtualSpace
	#		#that tells us newly lost, left, and hidden items
	#		#although it needs to match our search criteria, so the
	#		#background search which runs in the cloud will be an
	#		#instance specific to us, running as an agent on our behalf


	#TODO: it would be better to have a Point.describe() to do
	#the point inner parts, and lookup the point in self.points,
	#and relate it via it's own copies of self.meta and self.data
	#which gets access to the dispatcher tables?

	def describe(self):
		"""print a dump of our connectivity"""
		trace("Node.describe")
		print("-" * 80)
		info = self.meta.getNodeInfo(self.addr.nodeId, self.addr.databaseId)
		if info == None:
			raise ValueError("Node has no info")

		print("NODE:" + info["name"] + "(" + str(self.owner.ownerId) + " " + info["id"] + ")") #self.owner.ownerId
		if info.has_key("state"):
			print("  state:" + info["state"])
		else:
			print("  state:(unknown:" + str(info) + ")")

		#TODO this gets a list of points from the id_database
		#this helps us get data about our followers for example
		#but is not enough to get intricate local routing for handlers?

		# so it might be better to drive it from points[] and lookup the
		# point rec when we need it for follow/attach/advertise states?

		print("FROM MEM:")
		for pointName in self.points:
			point = self.points[pointName]
			path = self.meta.getPath(point.addr)
			trace("  name:" + str(pointName) + " point:" + str(point) + " path:" + path)
		#TODO handler links here?

		# ROUTING (for the whole Node)
		# All routing goes into two dispatchers, one in self.meta, one in self.data
		# This means that we can't get at it from Producer() and Consumer() directly
		print("ROUTING:")
		print("meta")
		print(self.meta.getConfig(indent=2))
		print("data")
		print(self.data.getConfig(indent=2))

		print("FROM DB:")
		pointRecs = self.meta.getPoints(self.owner.ownerId, self.nodeId) #self.owner.ownerId

		#TODO: delegate this to Point and call it for each point found
		if pointRecs != None:
			for pointRec in pointRecs:
				pointId = pointRec["id"] #self.owner.ownerId vvv
				print("  POINT:" + pointRec["name"] + "(" + str(self.owner.ownerId) + " " + str(self.nodeId) + " " + str(
					pointId) + ")")
				if pointRec.has_key("state"):
					print("    state:" + pointRec["state"])
				pointType = pointRec["pointType"]
				trace("TODO, describe Point")

		print("-" * 80)
		print("\n")




# POINT ----------------------------------------------------------------
# This is the GENERIC pointType

# are there sub types PointIn and PointOut???
# if so, these will be mapped to from the XXXLocal and XXXRemote
# for each XXX sub point type???

# an EmptyPoint is not routed to any application handler, its a placeholder before the app starts,
# but provides basic bind functionality to allow connectivity in both directions into the VirtualSpace.

# TODO this might be the base class of all Point's, not sure yet.
# it's actually a non routed point.
# hmm, feels like we should try to phase this out???

class EmptyPoint():
	def __init__(self, pointType, endType, ownerId, nodeId, pointName, pointId, meta, databaseId):
		self.pointType = pointType
		self.pointName = pointName
		###Need to pass databaseId here, or a ref to owner, but if we set it, it thinks it is remote
		#may need extra detection at a lower layer to compare with "our databaseId"
		#where it runs the filter for NODE.
		self.addr = Address(ownerId, nodeId, pointId, databaseId=databaseId)
		self.meta = meta
		# self.node     = None #TODO? parent?
		self.endType = endType
		self.bindType = None


	def __repr__(self):
		ids = str(self.addr.ownerId) + " " + str(self.addr.databaseId) + "." + str(self.addr.nodeId) + " " + str(self.addr.pointId)
		return "EmptyPoint!" + str(self.pointType) + "(" + ids + ") endType:" + str(self.endType) + " bindType:" + str(
			self.bindType)


	def advertise(self):  # DRY Point
		# trace("Point.advertise")
		self.meta.advertise(self.addr.pointId)


	def handleWhoisRequest(self, src, pointName):
		#trace("EmptyPoint.handleWhoisRequest: src=" + str(src) + " " + str(pointName))
		self.sendWhoisResponse(src)


	def sendWhoisResponse(self, dst):
		#trace("# EmptyPoint.sendWhoisResponse:" + str(self.addr) + " " + str(dst) + " " + str(self.pointName))
		self.meta.iAmPoint(self.addr.ownerId, self.addr.databaseId, self.addr.nodeId, self.addr.pointId, self.pointName, dst)


	def bind(self, bindType):  # DRY Point
		trace("# EmptyPoint.bind:" + str(self.pointName) + " " + str(bindType))
		# This is the generic form of follow() and attach()
		raise ValueError("Trying to bind to an empty point - do we need this????")

		if self.bindType != None:
			raise ValueError("Cannot bind an already bound point")

		pointId = self.meta.getPointId(self.addr.ownerId, self.addr.nodeId, self.pointName, databaseId=self.owner.databaseId)
		self.addr.pointId = pointId
		self.meta.bind(bindType, self.addr.ownerId, self.addr.databaseId, self.addr.nodeId, self.addr.pointId)  # THEM
		self.bindType = bindType



#TODO:REFACTOR - add a Node parameter to constructor, and simplify the addr references.
class Point():
	# pointType
	GENERIC = "GENERIC"
	# FEED      = "FEED"
	# INDICATOR = "INDICATOR"
	#CONTROL   = "CONTROL"

	# endType
	LOCAL = "LOCAL"
	REMOTE = "REMOTE"

	ONE_TO_MANY = "ONE_TO_MANY"
	MANY_TO_ONE = "MANY_TO_ONE"
	#ONE_TO_ONE   = "ONE_TO_ONE"
	#MANY_TO_MANY = "MANY_TO_MANY"

	def __init__(self, endType, ownerId, nodeId, pointName, pointId, meta, data, databaseId):
		self.pointName = pointName
		self.addr = Address(ownerId, nodeId, pointId, databaseId=databaseId)
		self.meta = meta
		self.data = data
		#self.node     = None #TODO? parent?
		self.endType = endType
		self.receive_fn = None
		self.bindType = None


	def __repr__(self):
		ids = str(self.addr.ownerId) + " " + str(self.addr.databaseId) + "." + str(self.addr.nodeId) + " " + str(self.addr.pointId)
		return "Point!" + str(self.endType) + "(" + ids + ") endType:" + str(self.endType) + " bindType:" + str(
			self.bindType)


	@staticmethod
	def metaCreate(pointType, endType, ownerId, databaseId, nodeId, pointName, meta, pointId=None):
		"""Create a meta record for this new point"""
		#trace("Point.metaCreate:" + str(pointType) + " " + str(endType) + " " + str(pointName))

		ownerId = str(ownerId)
		nodeId = str(nodeId)
		if pointId != None:
			pointId = str(pointId)

		pointId = meta.createPoint(pointType=pointType, pointName=pointName)

		# An EmptyPoint is a placeholder until the in-memory representation is created
		# it allows other node points to bind() to it
		# It's a bit like a sleeping Point
		p = EmptyPoint(pointType, endType, ownerId, nodeId, pointName, pointId, meta, databaseId=databaseId)
		return p


	@staticmethod
	def metaRestore(pointType, endType, ownerId, nodeId, pointName, pointId, meta, data, databaseId):
		"""Restore a point into memory, from the meta record"""
		#trace("Point.metaRestore:" + str(pointType) + " " + str(endType) + " " + str(pointName))

		if databaseId == None:
			trace("warning: Point.metaRestore no databaseId, endType:" + str(endType))
		if pointType == Point.GENERIC:
			p = Point(endType, ownerId, nodeId, pointName, pointId, meta=meta, data=data, databaseId=databaseId)

		#elif pointType == Point.FEED:
		#	p = Feed(endType, ownerId, nodeId, pointName, pointId, meta=meta, data=data)
		#
		#elif pointType == Point.INDICATOR:
		#	p = Indicator(endType, ownerId, nodeId, pointName, pointId, meta=meta, data=data)
		#
		#elif pointType == Point.CONTROL:
		#	p = Control(endType, ownerId, nodeId, pointName, pointId, meta=meta, data=data)
		#
		else:
			raise ValueError("Unknown pointType:" + str(pointType))

		if endType != Point.REMOTE:
			if pointId == None:
				# look to see if the number is already known
				pointId = meta.getPointId(ownerId=ownerId, nodeId=nodeId, pointName=pointName, databaseId=databaseId)
				if pointId == None:  # not known
					raise ValueError(
						"Cant find metadata for:(" + str(ownerId) + " " + str(nodeId) + " " + pointName + ")")
					# create a new pointId
					pointId = meta.createPoint(pointName, pointType=pointType)

			p.addr.pointId = pointId

		# pass all metadata to the point
		anyAddr = Address.EMPTY
		meta.registerListener(None, anyAddr, anyAddr, p.handleMeta)

		# pass relevant data payloads to the point
		#TODO: is this right, for all point types and ent types??
		#src = Address(ownerId, nodeId, pointId)
		#dst = Address()
		#data.registerListener("data.payload", src, dst, p.handleReceive)

		return p


	def setCallbacks(self, receive):
		"""Knit up any supported callbacks"""
		#TODO might want to use kwargs, and override in subclass
		#so that subclass police's which callbacks it accepts.

		if receive != None:
			self.setReceiveHandler(receive)
		#trace("registered receive:" + str(receive))


	def setReceiveHandler(self, handler):
		self.receive_fn = handler


	def share(self, data):
		# a useful vocabulary redirector
		self.send(data)


	def ask(self, data):
		# a useful vocabulary redirector
		self.send(data)


	def tell(self, data):
		# a useful vocabularly redirector
		self.send(data)


	def send(self, data):  # outgoing send() unicast
		#trace("# Point.send: me:" + str(self) + " myaddr:" + str(self.addr))

		if self.endType == Point.REMOTE:  # addr is dst addr
			databaseId = self.addr.databaseId
			#trace("# Point.send self.addr.databaseId:" + str(self.addr.databaseId))
			self.data.sendto(self.addr.ownerId, databaseId, self.addr.nodeId, self.addr.pointId, data=data)

		elif self.endType == Point.LOCAL:  # addr is src addr
			self.data.send(data=data, fromPointId=self.addr.pointId)

		else:
			trace("warning: unhandled send")


	def advertise(self):  #DRY EmptyPoint
		#trace("Point.advertise")
		self.meta.advertise(self.addr.pointId)


	def follow(self):
		# A useful vocabulary redirector
		self.bind(Point.ONE_TO_MANY)

	def attach(self):
		# A useful vocabulary redirector
		self.bind(Point.MANY_TO_ONE)

	def bind(self, bindType):  #DRY: EmptyPoint
		#trace("Point.bind:" + str(self.pointName) + " " + str(bindType))
		# This is the generic form of follow() and attach()

		if self.bindType != None:
			raise ValueError("Cannot bind an already bound point")

		#TODO this looks like the wrong addresses???
		#trace("  me:" + str(self))

		pointId = self.meta.getPointId(self.addr.ownerId, self.addr.nodeId, self.pointName, databaseId=self.addr.databaseId)
		self.addr.pointId = pointId
		self.meta.bind(bindType, self.addr.ownerId, self.addr.databaseId, self.addr.nodeId, self.addr.pointId)
		self.bindType = bindType
		#trace("Point.bind: waiting for bind to succeed")
		self.meta.waitBind(bindType, self.addr.ownerId, self.addr.databaseId, self.addr.nodeId, self.addr.pointId)


	#def metaUnbind(self):
	#	pass #TODO common code here - need to write this still
	# this is the generic form of unfollow() and release()

	#def metaUnadvertise(self):
	#	self.meta.hide(self.pointId)

	#def metaRemove(self):
	#	self.meta.remove(self.pointId)


	def handleMeta(self, info, data):
		#trace("Point.handleMeta:" + str(info) + " " + str(data))
		# FILTER
		if not info.msg.startswith("meta."):
			#trace("not a meta message:" + info.msg)
			return  # NOT HANDLED

		if not (info.msg.endswith(".req") or info.msg.endswith(".ind")):
			#trace("not a meta request:" + info.msg)
			return  # NOT HANDLED

		# we only process meta messages for this pointId
		#trace("filter? us:(" + str(self.addr) + " sender:" + str(info))
		if info.dst.pointId == None:
			return  # NOT HANDLED
		#TODO: If this is a remote, then self.addr is the remote address
		if not Address.match(self.addr, info.dst):
			return  # NOT HANDLED
		#trace("filter match Point")


		# DECODE
		verb = info.msg[5:-4]  # Get the middle verb
		msgtype = info.msg[-3:] # last 3 always the type

		self.dispatch(verb, msgtype, info.src, info.dst, data)


	def dispatch(self, verb, msgtype, src, dst, data):
		#TODO must be extended by the subclass?
		if verb == "bind" and msgtype == "ind":
			bindType = data
			self.handleBindIndication(src, dst, bindType)

		#TODO: is this ever handled here? WHOIS.REQ is sent to an Owner
		elif verb == "whois" and msgtype == "req":
			#nodeName = data
			#self.handleWhoisRequest(src, nodeName)
			raise ValueError("Did not expect to be here???")

		elif verb == "whois" and msgtype == "rsp":
			self.handleWhoisResponse(src, data)


	def handleWhoisRequest(self, src, pointName):
		#trace("Point.handleWhoisRequest: src=" + str(src) + " pointName=" + str(pointName))
		self.sendWhoisResponse(src)


	def sendWhoisResponse(self, dst):
		#trace("Point.sendWhoisResponse:" + str(self.addr) + " " + str(dst) + " " + str(self.pointName))
		self.meta.iAmPoint(self.addr.ownerId, self.addr.databaseId, self.addr.nodeId, self.addr.pointId, self.pointName, dst)


	def handleBindIndication(self, src, dst, bindType):
		#trace("Point.handleBindIndication: src=" + str(src) + "dst=" + str(dst) + " bindType=" + str(bindType))

		if bindType == Point.ONE_TO_MANY:
			if self.endType == Point.LOCAL: # local end of a follow does nothing
				#trace("1:N bind - FOLLOW")
				# by default we accept all bind requests of type follow
				if not self.meta.isBound(src, dst, bindType): # already in db?
					#trace("sending bindConfirm from:" + str(self) + " endType:" + str(self.endType))
					self.meta.bindConfirm(src, dst, bindType)

			elif self.endType == Point.REMOTE: # remote end of a follow has to listen for data
				#trace("TODO should atttempt data.payload registration for dynamic follow")
				#self.data.registerListener("data.payload", src, dst, self.handleReceive, duplicate=Dispatcher.SQUASH)
				pass

		elif bindType == Point.MANY_TO_ONE:
			if self.endType == Point.LOCAL: # local end of an attach has to register for data
				#trace("N:1 bind - ATTACH")
				# by default we accept all bind requests of type attach
				#trace("data.payload registration for dynamic attach")
				self.data.registerListener("data.payload", src, dst, self.handleReceive, duplicate=Dispatcher.SQUASH)

				if not self.meta.isBound(src, dst, bindType): # already in db?
					#trace("sending bindConfirm from:" + str(self) + " endType:" + str(self.endType))
					self.meta.bindConfirm(src, dst, bindType)

			elif self.endType == Point.REMOTE: # remote end of an attach is sender, do nothing
				#trace("remote end of attach, does not register")
				pass

		else:
			trace("warning: Unknown bind type:" + str(bindType))

	def handleReceive(self, info, data):  # incoming receive()
		#trace("Point.handleReceive:" + str(info) + " " + str(data))
		if self.receive_fn != None:
			self.receive_fn(info, data)
		else:
			trace("warning: DATA when no receive handler:" + str(info) + " " + str(data))



# APP WRAPPER ----------------------------------------------------------
# This defines an interface for apps, and helps with automating
# the startup process. This is helpful to turn a non object oriented
# module into an object (it's a bit like an interface), and can be
# used with objects or with modules.

class AppWrapper():
	def __init__(self, ownerName, nodeName, app):
		self.ownerName = ownerName
		self.nodeName = nodeName
		self.app = app
		self.node = None
		self.first = None


	def warning(self, msg):
		print("warning:" + str(msg))

	def create(self):
		# must be a create()
		return self.app.create()

	def bind(self):
		# bind() is optional
		try:
			self.app.bind()
		except AttributeError:
			self.warning("app has no bind()")

	def restore(self):
		# must be a restore()
		return self.app.restore()

	def wakeup(self):
		# wakeup() is optional
		try:
			self.app.wakeup()
		except AttributeError:
			self.warning("app has no wakeup()")
			# so force a call to node.wakeup()
			self.node.wakeup()

	def loop(self):
		# loop() is optional
		try:
			self.node.loopUsed = False
			self.app.loop()
			if not self.node.loopUsed:
				trace("warning:" + str(self.nodeName) + ": app.loop() did not call Node.loop()")
		except AttributeError:
			self.warning("app has no loop()")
			self.node.loop() # so call it anyway


	def sleep(self):
		# sleep() is optional
		try:
			self.app.sleep()
		except AttributeError:
			self.warning("app has no sleep()")
			# so force a call to node.sleep()
			self.node.sleep()


# APP RUNNER -----------------------------------------------------------			
# This actually automates the startup process.

class AppRunner():
	@staticmethod
	def run(app, ownerName=None, rate=1, debug=False, dbPath=None):
		APPS = [app]
		AppRunner.runAll(APPS, ownerName=ownerName, rate=rate, debug=debug, dbPath=dbPath)

	@staticmethod
	def runAll(applist, ownerName=None, first=False, rate=1, debug=False, dbPath=None):
		import time
		# SIGNUP if required
		if debug:
			trace("-------- signup:" + str(ownerName))
		owner = Owner.use(ownerName, dbPath=dbPath)

		# Create wrapped versions of all apps in the list,
		# in case of missing optional methods
		apps = []
		for a in applist:
			#app is a tuple of (name, appref)
			nodeName = a[0]
			app = a[1]
			thisApp = AppWrapper(ownerName, nodeName, app)
			apps.append(thisApp)


		# CREATE nodes
		# first time a node connects to the IOT, it has to configure
		# it's local producers and consumers, and knit up to any remote
		# producers and consumers it needs. This is the DEPLOY process,
		# i.e. the FIRST_RUN or CONFIGURE phase.

		# this will include all advertise()'s
		# this might be template driven, i.e. the virtual representation
		# might be created from a template, and the node just validates
		# itself against that template then creates everything if it
		# can achieve what it defines. e.g. 10000 fridges all the same.
		# only serial number varies.

		# Note that all local setup needs to be done first, before any
		# remote setup. This is so that producers and consumers are created
		# before an attempt is made to bind to them. This is really clunky,
		# we might find a way through "waiting" for a node to be able to
		# do all the startup in one go - although this is fraught with
		# deadlock issues so should be avoided.
		#
		# Note, this is simulation specific though. Any one node would
		# do all it's local configuration first, then its knitting or
		# its re-knitting of callbacks. Don't worry too much about it
		# here, but we need a way in this simulator to be able to do all
		# local setups first, then all remote setups, otherwise we get
		# strange deadlock.

		for app in apps:
			state = owner.getStateForNode(app.nodeName)
			if state == None:  # not yet created
				if debug:
					trace("-------- create:" + app.nodeName)
				node = app.create()
				if node == None:
					raise ValueError("Must return the node from create()")
				app.node = node
				app.node.loop()  # allow some message processing

		# BIND
		# Bind to any remote nodes, by doing follow() and attach()
		# this is all about joining up to other virtual nodes, i.e.
		# following and sharing. This would only be done once normally
		# as part of the second phase of configuration.
		#
		#for app in appss:
		#	if not app.isConfigured():
		#		app.bind()

		# At the moment, we do this every time the code starts. The Node
		# abstraction works out that there is nothing new to do.

		for app in apps:
			state = owner.getStateForNode(app.nodeName)
			#trace("state:" + state)
			if state == Node.CREATED:
				if debug:
					trace("-------- bind:" + app.nodeName)
				app.bind()
				app.node.setState(Node.BOUND)
				app.node.loop()


		# RESTORE
		# restore the node and it's point bindings, ready for use
		# every pass through the AppRunner must do this every time

		for app in apps:
			if debug:
				trace("-------- restore:" + app.nodeName)
			node = app.restore()
			if node == None:
				raise ValueError("Must return the node from restore()")
			app.node = node
			app.node.loop()


		# RUN

		# Once a node has been CONFIGURED, it has to "wakeup" so that it's
		# virtual representation knows that it is connected to this real
		# node. If RESTARTING, it still has to "wakeup".
		#
		# Somewhere here, we need to be able to knit (or re-knit) callbacks
		# to handlers in the code. Programmatically, local_setup and
		# remote_setup do this at the moment, however it would make sense
		# to defer callback knitting so that it can easily be done on restore.

		for app in apps:
			if debug:
				trace("-------- wakeup:" + app.nodeName)
			app.nloops = 0
			app.wakeup()
			app.node.loop()  # allow some message processing


		try: # main loop
			while True:
				time.sleep(rate)
				for app in apps:
					if debug == True:
						trace("-------- loop:" + app.nodeName)
					app.loop()  # this is both nodapp.loop and Node.loop
					app.nloops += 1
					if app.nloops == 3 and debug:
						app.node.describe()
		finally:
			print("*" * 80)
			print("exception in loop - trying to sleep")
			print("*" * 80)

			for app in apps:
				if debug:
					trace("-------- sleep:" + app.nodeName)
				app.sleep()
				app.node.loop() # allow any final message processing


# END
