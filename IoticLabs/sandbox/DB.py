# DB.py  01/11/14  D.J.Whale
#
# This is the local database of useful information.
# The database itself is distributed, but this is the local copy.

import RFC822
from Address import StrAddress

DEFAULT_DBNAME = "test"


# CONFIGURATION --------------------------------------------------------

def trace(msg):
	print(str(msg))

def warning(msg):
	print("warning:" + str(msg))
	

# ID DATABASE ----------------------------------------------------------

class IdDatabase():
	@staticmethod
	def exists(dbPath):
		"""Does this database exist or not?"""
		if dbPath == None:
			dbPath = DEFAULT_DBNAME
		dbName = dbPath + ".db"
		import os
		return os.path.isfile(dbName)


	@staticmethod
	def create(dbPath, databaseId):
		"""Create a brand new database and write databaseId rec to it"""

		# Create an empty database first
		db = RFC822.RFC822Database(dbPath + ".db", keyName="id")
		db.create()
		db = None

		# Now write the databaseId to it as the first rec
		db = IdDatabase(dbPath)
		db.open(cache=False)
		db.setDatabaseId(databaseId)
		db.close()


	def __init__(self, dbPath=None):
		if dbPath == None:
			dbPath = DEFAULT_DBNAME
		self.dbPath = dbPath
		self.db = RFC822.RFC822Database(dbPath + ".db", keyName="id")


	# LOW LEVEL ACCESS -------------------------------------------------
	
	def clear(self):
		"""clear the database"""
		self.db.clear()


	def open(self, cache=True):
		self.db.open()
		if cache:
			self.databaseId = self.getDatabaseId()


	def close(self):
		self.db.close()


	def writeId(self, addr, typeName, name):
		f = open(self.dbPath + ".id", "a")
		f.write(str(addr) + " " + typeName + " " + name + "\n")
		f.close()
		
		
	# CREATION ---------------------------------------------------------

	##OWNER


	def createOwner(self, ownerName, ownerId=None):
		"""Create a new owner in our database"""
		# Note, auto-numbering owners is "tolerated" at the moment
		# but we will need an external allocation scheme later.
		# This won't work multi-database instance.

		actualOwnerId = self.getOwnerId(ownerName)
		if actualOwnerId != None: # already exists
			raise ValueError("Owner already exists:" 
			+ str(ownerName) + " " + str(actualOwnerId))

		# Requesting a specific ownerId?
		if ownerId != None: # yes, want this specific ownerId
			if actualOwnerId != None: # already exists
				if actualOwnerId != ownerId:
					raise ValueError("Owner already exists as different id:"
					+ str(ownerName) + " " + str(actualOwnerId))
				else: # already exists as that ownerId
					return ownerId
			else: # ownerName does not exist
				pass
		else: # no, use any ownerId
			if actualOwnerId != None: # already exists
				return actualOwnerId
			else: # ownerName does not exist
				pass

		# At the moment, if we create an owner rec with the databaseId in it,
		# it means it was initiated by that database. Not sure if we will need this
		# eventually, but at the moment Node.restore needs it to get the databaseId
		# that is propagated to all it's local nodes.
		newOwnerId = self.createOwnerRec(ownerName, self.databaseId, ownerId, isLocal=True)
		return newOwnerId


	def rememberOwner(self, ownerName, ownerId, databaseId):
		"""make an address cache record for any owner"""
		#trace("rememberOwner:" + str(ownerId) + " " + str(databaseId) + " " + str(ownerName))

		if ownerId == None:
			raise ValueError("Must provide an ownerId")
		#Owner is not really associated with a database, but we might
		#want to keep a local list of databases that we know have
		#told us they have that owner record themselves.
		#if databaseId == None:
		#  raise ValueError("Must provide a databaseId")

		# does this ownerName already exist in our cached addresses in DB?
		actualOwnerId = self.getOwnerId(ownerName)
		if actualOwnerId != None:
			# we will probably receive our own meta.signup messages at moment
			#warning("There is already an ownerId for:" + ownerName)
			#raise ValueError("There is already an ownerId for:" + ownerName)
			return actualOwnerId # so, ignore it for now

		ownerId = self.createOwnerRec(ownerName, databaseId, ownerId, isLocal=False)
		return ownerId


	# TODO putting databaseId in Owner rec is still required by using interface,
	# but we might have to deprecate it later as it is a false link in remote addr cases.
	# unless we use the same addressing idea as nodeAddr, so any cpu could create an owner
	# and it would be made unique by it's databaseId (but name must be unique).
	# not sure about that yet.
	def createOwnerRec(self, ownerName, databaseId, ownerId=None, isLocal=False):
		"""Create a record in db for an owner"""
		#This might be a locally created owner, or an address reference to an owner

		rec = {
			"type":       "OWNER",
			"name":       ownerName,
			"databaseId": databaseId
		}

		if isLocal:
			if ownerId != None:
				rec["id"] = ownerId

		newOwnerId = self.db.write(rec, morekeys=["ownerId"])
		if isLocal:
			# Only locally created ownerId's get written to our id cache
			self.writeId(StrAddress(newOwnerId), "OWNER", ownerName)
		return newOwnerId


	##NODE

	def createNode(self, ownerId, databaseId, nodeId, nodeName):
		"""Create a new node, locally"""

		actualNodeId = self.getNodeId(ownerId, nodeName)
		if actualNodeId != None: # already exists
			raise ValueError("Node already exists:" + str(nodeName) + " " + str(actualNodeId))

		# Requesting a specific nodeId?
		if nodeId != None: # yes, want this specific nodeId
			if actualNodeId != None: # already exists
				if actualNodeId != nodeId:
					raise ValueError("Node already exists as different id:"
					+ str(nodeName) + " " + str(actualNodeId))
				else: # already exists as that nodeId
					return nodeId
			else: # nodeName does not exist
				pass
		else: # no, use any nodeId
			if actualNodeId != None: # already exists
				return actualNodeId
			else: # nodeName does not exist
				pass

		newNodeId = self.createNodeRec(ownerId, databaseId, nodeId, nodeName, isLocal=True)
		return newNodeId


	def rememberNode(self, ownerId, nodeName, nodeId, databaseId):
		"""update the node address cache with someone else's node info"""
		#trace("db.rememberNode:" + str(ownerId) + " " + str(databaseId) + " " + str(nodeId) + " " + str(nodeName))

		# does this nodeName already exist in our cached addresses in DB?
		actualNodeAddr = self.getNodeAddr(ownerId, nodeName)
		if actualNodeAddr != None:
			# we will probably receive our own meta.signup messages at moment
			#warning("There is already an nodeAddr for:" + nodeName)
			#raise ValueError("There is already an nodAddr for:" + nodeName)
			return actualNodeAddr # so, ignore it for now

		self.createNodeRec(ownerId, nodeId, databaseId, nodeName, isLocal=False)


	def createNodeRec(self, ownerId, nodeId, databaseId, nodeName, isLocal=False):
		"""low-level create a brand new nodeId, fail if it already exists"""

		rec = {
			"type":      "NODE",
			"ownerId":    ownerId,
			"name":       nodeName,
			"databaseId": databaseId
		}
		if isLocal:
			if nodeId != None: # forcing a nodeId
				rec["id"] = nodeId
			newNodeId = self.db.write(rec, morekeys=["nodeId"])
			self.writeId(StrAddress(ownerId, newNodeId, databaseId=self.databaseId), "NODE", nodeName)

		else: # remote
			if nodeId == None:
				raise ValueError("Remote Node requires a nodeId")
			rec["nodeId"] = nodeId
			newNodeId = self.db.write(rec)

		return newNodeId


	#TODO how is this different from rememberNode???
	def createRemoteNode(self, ownerId, databaseId, nodeId, nodeName):
		"""Create a new node, as a reference to a remote node"""
		#trace("createRemoteNode:" + str(ownerId) + " " + str(databaseId) + " " + str(nodeId) + " " + str(nodeName))

		# If already exists, do nothing with it
		actualNodeId = self.getNodeId(ownerId, nodeName)
		if actualNodeId != None: # already exists
			#This is ok, as there may be latent whois.rsp messages, or another node may have already
			#written this record to a shared database.
			#warning("Node already exists, but ok:" + str(ownerId) + " " + str(nodeName) + " nodeId:" + str(actualNodeId))
			return

		self.createRemoteNodeRec(ownerId, databaseId, nodeId, nodeName)


	#TODO how is this different from createNodeRec???
	def createRemoteNodeRec(self, ownerId, databaseId, nodeId, nodeName):
		"""Create and write a remote NODE record to our DB"""

		rec = {
			"type":      "NODE",
			"ownerId":    ownerId,
			"databaseId": databaseId,
			"nodeId":     nodeId,
			"name":       nodeName
		}
		localNodeId = self.db.write(rec)
		#trace("remote Node written, nodeAddr:" + str(databaseId) + "." + str(nodeId) + " localNodeId:" + str(localNodeId))
		return localNodeId


	##POINT

	def createPoint(self, ownerId, nodeId, pointType, pointName, pointId=None):
		"""low-level create a brand new pointId, fail if it already exists"""
		# Points are always created in the local database, so no databaseId is needed
		
		# does this pointName already exist?
		# Don't need databaseId, this is a local node
		actualPointId = self.getPointId(ownerId, nodeId, pointName, databaseId=self.databaseId)
		if actualPointId != None: # already exists
			raise ValueError("Point already exists:" 
			+ str(ownerId) + " " + str(actualPointId))

		# Requesting a specific nodeId?
		if pointId != None: # yes, want this specific pointId
			if actualPointId != None: # already exists
				if actualPointId != pointId:
					raise ValueError("Point already exists as different id:"
					+ str(pointName) + " " + str(actualPointId))
				else: # already exists as that pointId
					return pointId
			else: # pointName does not exist
				pass
		else: # no, use any pointId
			if actualPointId != None: # already exists
				return actualPointId
			else: # pointName does not exist
				pass

		newPointId = self.createPointRec(ownerId, nodeId, pointType, pointName, pointId, self.databaseId, isLocal=True)
		return newPointId


	def rememberPoint(self, ownerId, nodeId, pointType, pointName, pointId, databaseId):
		"""high-level point address caching"""

		# does this pointName already exist in our cached addresses in DB?
		actualPointId = self.getPointId(ownerId, nodeId, pointName, databaseId)
		if actualPointId != None:
			# we will probably receive our own meta.signup messages at moment
			#warning("There is already an pointId for:" + pointName)
			#raise ValueError("There is already an pointId for:" + pointName)
			return actualPointId # so, ignore it for now

		pointId = self.createPointRec(ownerId, nodeId, pointType, pointName, pointId, databaseId, isLocal=False)
		return pointId


	def createPointRec(self, ownerId, nodeId, pointType, pointName, pointId, databaseId, isLocal=False):
		"""Low level POINT record creation"""
		rec = {
			"type":      'POINT',
			"ownerId":   ownerId,
			"databaseId":databaseId,
			"nodeId":    nodeId,
			'name':      pointName,
			"pointType": pointType
		}
		if isLocal:
			if pointId != None:
				rec["id"] = pointId

		newPointId = self.db.write(rec, morekeys=["pointId"])
		if isLocal:
			self.writeId(StrAddress(ownerId, nodeId, newPointId, databaseId=self.databaseId), "POINT", pointName)
		return newPointId


	#TODO how is this different from rememberPoint???
	def createRemotePoint(self, ownerId, databaseId, nodeId, pointId, pointName):
		"""Create a new point, as a reference to a remote point"""
		#trace("createRemotePoint:" + str(ownerId) + " " + str(databaseId) + " " + str(nodeId) + " " + str(pointId) + " " + str(pointName))

		# If already exists, do nothing with it
		actualPointId = self.getPointId(ownerId, nodeId, pointName, databaseId=databaseId)
		if actualPointId != None: # already exists
			#This is ok, as there may be latent whois.rsp messages, or another node may have already
			#written this record to a shared database.
			#warning("Point already exists, but ok:" + str(ownerId) + " " + str(nodeId) + " " + str(pointId) + " " + str(pointName))
			return

		self.createRemotePointRec(ownerId, databaseId, nodeId, pointId, pointName)


	#TODO how is this different from createPointRec???
	def createRemotePointRec(self, ownerId, databaseId, nodeId, pointId, pointName):
		"""Create and write a remote POINT record to our DB"""

		rec = {
			"type":      "POINT",
			"ownerId":    ownerId,
			"databaseId": databaseId,
			"nodeId":     nodeId,
			"pointId":    pointId,
			"name":       pointName,
			"pointType":  "GENERIC" #TODO will have to advertise as part of WHOIS
		}
		localPointId = self.db.write(rec)
		#trace("remote Point written. localPointId:" + str(localPointId))
		return localPointId


	# GETTERS ----------------------------------------------------------

	##DATABASE

	def getDatabaseId(self):
		rec = self.db.find({"type": "DATABASE"}, limit=1)
		if rec == None:
			raise ValueError("There is no databaseId for this database")
		return rec["databaseId"]

	##OWNER

	def ownerExists(self, ownerName):
		#TODO: If not in local db, this will always return False, but might be in another db???
		#This is not a substitute for WHOIS processing.
		rec = self.db.find({"type":"OWNER", "name":str(ownerName)}, limit=1)
		return (rec != None)


	def getOwnerId(self, ownerName):
		"""Get the ownerId for this ownerName, None if not known"""
		rec = self.db.find({"type": "OWNER", "name":str(ownerName)}, limit=1)
		if rec == None:
			return None
		return rec["ownerId"]


	def getOwnerName(self, ownerId):
		"""Get the ownerName for this ownerId, None if not known"""
		rec = self.db.find({"type": "OWNER", "ownerId":str(ownerId)}, limit=1)
		if rec == None:
			raise ValueError("Unknown ownerId:" + str(ownerId))
		return rec["name"]


	def getOwnerNames(self):
		"""Get a list of owner names"""
		recs = self.db.find({"type":"OWNER"})
		ownerNames = []
		for r in recs:
			ownerNames.append(r["name"])
		return ownerNames


	def getAllOwnersMap(self):
		"""Get a map view of ownerId->ownerName"""
		recs = self.db.find({"type":"OWNER"})
		owners = {}
		for rec in recs:
			id         = rec["ownerId"]
			name       = rec["name"]
			owners[id] = name
		return owners



	##NODE

	def nodeExists(self, ownerId, nodeName):
		#TODO:If not in local db, this will always return False, but might be in another db???
		#This is not a substitute for WHOIS processing.
		rec = self.db.find({"type":"NODE", "ownerId" : str(ownerId), "name":str(nodeName)}, limit=1)
		return (rec != None)


	def getNodeId(self, ownerId, nodeName):
		"""Get the nodeId for this owner associated with this nodeName"""
		# Note, only use this to get the localId, not for remote nodes via a NODE ref.

		#trace("DB.getNodeId: ownerId:" + str(ownerId) + " nodeName:" + str(nodeName))
		if ownerId == None:
			raise ValueError("no ownerId")
		if nodeName == None:
			raise ValueError("no nodeName")
		rec = self.db.find({"type": "NODE", "ownerId":str(ownerId), "name":str(nodeName)}, limit=1)

		if rec == None:
			return None # NOT FOUND

		nodeId = rec["nodeId"]
		return nodeId


	def getNodeAddr(self, ownerId, nodeName):
		"""Get a nodeAddr for any node for this owner"""
		if ownerId == None:
			raise ValueError("no ownerId")
		if nodeName == None:
			raise ValueError("no nodeName")
		rec = self.db.find({"type": "NODE", "ownerId":str(ownerId), "name":str(nodeName)}, limit=1)

		if rec == None:
			return None

		nodeId = rec["nodeId"]

		if rec.has_key("databaseId"):
			databaseId = rec["databaseId"]
			#trace("remote databaseId returned")
		else:
			databaseId = None # should be self.owner.databaseId, to be complete?
			#warning("local databaseId returned")
		return (databaseId, nodeId)


	def getNodeName(self, ownerId, nodeId, databaseId):
		"""Get the nodeName for this nodeId, None if not known"""
		criteria = {
			"type":      "NODE",
			"ownerId":    str(ownerId),
			"databaseId": str(databaseId),
			"nodeId":     str(nodeId)
		}
		rec = self.db.find(criteria, limit=1)
		if rec == None:
			raise ValueError("Unknown nodeId:" + str(ownerId) + " " + str(databaseId) + "." + str(nodeId))
		return rec["name"]


	def getNodeRec(self, ownerId, nodeId, databaseId):
		#trace("DB.getNodeRec:" + str(ownerId) + " " + str(nodeId))
		if ownerId == None:
			raise ValueError("must supply an ownerId")
		if nodeId == None:
			raise ValueError("must supply a nodeId")
		if databaseId == None:
			raise ValueError("must supply a databaseId")

		criteria = {
			"type":      "NODE",
			"ownerId":    str(ownerId),
			"databaseId": str(databaseId),
			"nodeId":     str(nodeId)
		}
		rec = self.db.find(criteria, limit=1)
		if rec == None:
			#trace(str(self.db.index))
			raise ValueError("Could not find node: (" + str(ownerId) + " " + str(databaseId) + "." + str(nodeId) + ")")
		return rec


	def getAllNodesMap(self):
		"""Get a map view of (ownerId, databaseId, nodeId) -> ownerName/nodeName"""
		recs = self.db.find({"type":"NODE"})
		nodes = {}
		for rec in recs:
			ownerId    = rec["ownerId"]
			databaseId = rec["databaseId"]
			nodeId     = rec["nodeId"]
			name       = rec["name"]
			addr = (ownerId, databaseId, nodeId)
			ownerName = self.getOwnerName(ownerId)
			nodes[addr] = ownerName + "/" + name
		return nodes


	####REORDER PARAMS
	def getNodeState(self, ownerId, nodeId, databaseId):
		rec = self.getNodeRec(ownerId, nodeId, databaseId=databaseId)
		if rec == None:
			return None
		return rec["state"]


	####REORDER PARAMS
	def getPointIds(self, ownerId, nodeId, databaseId, limit=1):
		"""Get the pointIds of all points on this node for this owner"""
		criteria = {
			"type":       "POINT",
			"ownerId":    str(ownerId),
			"databaseId": str(databaseId),
			"nodeId":     str(nodeId)
		}
		recs = self.db.find(criteria, limit=limit)
		# get out all the ids
		ids = []
		for rec in recs:
			ids.append(rec["pointId"])
		return ids


	####REORDER PARAMS
	def getPointRecs(self, ownerId, nodeId, databaseId, limit=None):
		"""Get the recs of all points on this node for this owner"""
		criteria = {
			"type":      "POINT",
			"ownerId":    str(ownerId),
			"databaseId": str(databaseId),
			"nodeId":     str(nodeId)
		}
		recs = self.db.find(criteria, limit=limit)
		return recs


	##POINT

	def pointExists(self, ownerId, nodeId, pointType, pointName, databaseId):
		criteria = {
			"type":      "POINT",
			"ownerId":    str(ownerId),
			"databaseId": str(databaseId),
			"nodeId":     str(nodeId),
			"pointType":  str(pointType),
			"name":       str(pointName)
		}
		rec = self.db.find(criteria, limit=1)
		return (rec != None)


	####REORDER PARAMS
	def getPointId(self, ownerId, nodeId, pointName, databaseId):
		"""Get the pointId for the pointName on this node for this owner"""
		#trace("DB.getPointId:" + str(ownerId) + " " + str(nodeId) + " " + str(pointName))
		criteria = {
			"type":       "POINT",
			"ownerId":    str(ownerId),
			"databaseId": str(databaseId),
			"nodeId":     str(nodeId),
			"name":       str(pointName)
		}
		rec=self.db.find(criteria, limit=1)
		if rec == None:
			#trace("DB.getPointId:NOT FOUND:" + str(ownerId) + " " + str(databaseId) + " " + str(nodeId) + " " + str(pointName))
			return None

		if rec.has_key("pointId"):
			# it is probably a remote point
			pointId = rec["pointId"]
			#trace("probably a remote pointId")
		else:
			# it is probably a local point
			pointId = rec["pointId"]
			#trace("probably a local pointId")
		return pointId


	def getPointName(self, ownerId, nodeId, pointId, databaseId):
		"""Get the name of a specific point"""
		criteria = {
			"type":      "POINT",
			"ownerId":    str(ownerId),
			"databaseId": str(databaseId),
			"nodeId":     str(nodeId),
			"pointId":    str(pointId)
		}
		rec = self.db.find(criteria, limit=1)
		if rec == None:
			return "(UnknownPoint:(" + str(ownerId) +" " + str(nodeId) + " " + str(pointId) + ")"
			#raise ValueError("No point: (" + str(ownerId) + " " + str(nodeId) + " " + str(pointId) + ")")
		return rec["name"]


	def getPointType(self, ownerId, nodeId, pointId, databaseId):
		"""Get the pointType for this point"""
		criteria = {
			"type":       "POINT",
			"ownerId":    str(ownerId),
			"databaseId": str(databaseId),
			"nodeId":     str(nodeId),
			"pointId":    str(pointId)
		}
		rec=self.db.find(criteria, limit=1)
		if rec != None:
			return rec["pointType"]
		raise ValueError("Unknown point:" + str(ownerId) + " " + str(databaseId) + "." + str(nodeId) + " " + str(pointId))


	def getPointRec(self, ownerId, nodeId, pointId, databaseId):
		"""Get the point rec for this point"""
		criteria = {
			"type":      "POINT",
			"ownerId":    str(ownerId),
			"databaseId": str(databaseId),
			"nodeId":     str(nodeId),
			"pointId":    str(pointId)
		}
		rec = self.db.find(criteria, limit=1)
		return rec


	def getAllPointsMap(self):
		"""Get a map view of (ownerId, databaseId, nodeId, pointId) -> pointName"""
		recs = self.db.find({"type":"POINT"})
		nodes = {}
		for rec in recs:
			ownerId    = rec["ownerId"]
			databaseId = rec["databaseId"]
			nodeId     = rec["nodeId"]
			pointId    = rec["pointId"]
			pointName  = rec["name"]
			pointAddr  = (ownerId, databaseId, nodeId, pointId)
			ownerName  = self.getOwnerName(ownerId)
			nodeName   = self.getNodeName(ownerId, nodeId, databaseId=databaseId)
			nodes[pointAddr] = ownerName + "/" + nodeName + "/" + pointName
		return nodes


	def isBound(self, src, dst, bindType):
		"""Test if a particular binding already exists"""
		criteria = {
			"type":"BIND",
			"bindType":str(bindType),
			"srcOwnerId":str(src.ownerId),
			"srcNodeId":str(src.nodeId),
			"dstOwnerId":str(dst.ownerId),
			"dstNodeId":str(dst.nodeId)
		}
		if src.pointId != None:
			criteria["srcPointId"] = str(src.pointId)
		if dst.pointId != None:
			criteria["dstPointId"] = str(dst.pointId)

		rec = self.db.find(criteria, limit=1)
		return (rec != None)


	def getBindingsFor(self, bindType, src=None, dst=None):
		"""Get all the bindings for this point address"""
		#trace("DB.getBindingsFor: src=" + str(src) + " " + str(bindType) + " dst=" + str(dst))

		criteria = {
			"type":         "BIND",
			"bindType":      str(bindType)
		}

		if src != None:
			if src.ownerId != None:
				criteria["srcOwnerId"]    = str(src.ownerId)
				if src.databaseId != None:
					criteria["srcDatabaseId"] = str(src.databaseId)
					criteria["srcNodeId"]     = str(src.nodeId)
					if src.pointId != None:
						criteria["srcPointId"]    = str(src.pointId)

	   	if dst != None:
			if dst.ownerId != None:
				criteria["dstOwnerId"]    = str(dst.ownerId)
				if dst.databaseId != None:
					criteria["dstDatabaseId"] = str(dst.databaseId)
					criteria["dstNodeId"]     = str(dst.nodeId)
					if dst.pointId != None:
						criteria["dstPointId"]    = str(dst.pointId)

		#trace("  using criteria:" + str(criteria))
		recs = self.db.find(criteria)
		#trace("  found recs:" + str(recs))
		return recs


	# SETTERS -----------------------------------------------------------------

	def setDatabaseId(self, databaseId):
		self.setDatabaseIdRec(databaseId)


	def setDatabaseIdRec(self, databaseId):
		self.writeId(databaseId, "DATABASE", self.dbPath + ".db")
		rec = {"type": "DATABASE", "databaseId": str(databaseId)}
		self.db.write(rec)


	# STATE MUTATORS ---------------------------------------------------

	def changeNodeState(self, ownerId, nodeId, newState):
		# Can only change local Node state, so databaseId is not needed
		self.changeNodeStateRec(ownerId, nodeId, newState)


	def changeNodeStateRec(self, ownerId, nodeId, newState):
		rec = self.db.find({"type": "NODE", "ownerId":str(ownerId), "nodeId":str(nodeId)}, limit=1)
		if rec == None:
			raise ValueError("no such node")
		id = rec["id"]
		rec["state"] = newState
		self.db.overwrite(id, rec)


	def changePointState(self, ownerId, nodeId, pointId, newState):
		# Can only change local point state, so databaseId is not needed
		self.changePointStateRec(ownerId, nodeId, pointId, newState)


	def changePointStateRec(self, ownerId, nodeId, pointId, newState):
		rec = self.db.find({"type": "POINT", "ownerId":str(ownerId), "nodeId":str(nodeId), "pointId":str(pointId)}, limit=1)
		if rec == None:
			raise ValueError("no such point:" + str(ownerId) + " " + str(nodeId) + " " + str(pointId))
		id = rec["id"]
		rec["state"] = newState
		self.db.overwrite(id, rec)


	# ACTION VERBS -----------------------------------------------------
		
	#TODO what if already advertised?
	#then leave unchanged
	def advertise(self, ownerId, nodeId, pointId, databaseId):
		# can only advertise local points, so no databaseId needed
		#trace("DB.advertise")
		#TODO should use databaseId too??
		self.advertiseRec(ownerId, nodeId, pointId, databaseId)


	def advertiseRec(self, ownerId, nodeId, pointId, databaseId):
		pass # temporarily disabled, broken
		#selector = {"type":"POINT", "ownerId":str(ownerId), "databaseId":str(databaseId), "nodeId":str(nodeId), "pointId":str(pointId)}
		#rec = self.db.find(selector, limit=1)
		#if rec == None:
		#	raise ValueError("Unknown point: (" + str(ownerId) + " ?." + str(nodeId) + " " + str(pointId) + ")")
		#rec["state"] = "ADVERTISED"
		#id = rec["id"]
		#self.db.overwrite(id, rec)


	#TODO what if already hidden?
	#then just leave unchanged
	def unadvertise(self, ownerId, nodeId, pointId):
		# can only unadvertise local Points, so no databaseId needed
		#trace("DB.hide")
		self.unadvertiseRec(ownerId, nodeId, pointId)


	def unadvertiseRec(self, ownerId, nodeId, pointId):
		pass # temporarily disabled, broken
		#selector = {"type":"POINT", "ownerId":str(ownerId), "nodeId":str(nodeId), "pointId":str(pointId)}
		#rec = self.db.find(selector, limit=1)
		#if rec == None:
		#	raise ValueError("Unknown point")
		#rec["state"] = "HIDDEN"
		#id = rec["id"]
		#self.db.overwrite(id, rec)


	def bind(self, bindType, srcOwnerId, srcDatabaseId, srcNodeId, srcPointId,
		dstOwnerId, dstDatabaseId, dstNodeId, dstPointId):
		#trace("DB.bind:"
		#	  +  "(" +str(srcOwnerId) + " " + str(srcDatabaseId) + "." + str(srcNodeId) + " " + str(srcPointId) + ")"
		#	  + " (" + str(dstOwnerId) + " " + str(dstDatabaseId) + "." + str(dstNodeId) + " " + str(dstPointId) + ")"
		#	  + " " + str(bindType))

		if bindType == "ONE_TO_MANY":
			# must swap src and dst addresses for a follow
			srcOwnerId,    dstOwnerId    = dstOwnerId,    srcOwnerId
			srcDatabaseId, dstDatabaseId = dstDatabaseId, srcDatabaseId
			srcNodeId,     dstNodeId     = dstNodeId,     srcNodeId
			srcPointId,    dstPointId    = dstPointId,    srcPointId

		self.bindRec(bindType, srcOwnerId, srcDatabaseId, srcNodeId, srcPointId,
					 dstOwnerId, dstDatabaseId, dstNodeId, dstPointId)


	def bindRec(self, bindType, srcOwnerId, srcDatabaseId, srcNodeId, srcPointId,
				dstOwnerId, dstDatabaseId, dstNodeId, dstPointId):
		
		# check if record already exists, if not, create it
		# Make pointId optional based on parameters
		newrec = {
			"type":          "BIND",
			"bindType":       str(bindType),
			"srcOwnerId":     str(srcOwnerId),
			"srcDatabaseId":  str(srcDatabaseId),
			"srcNodeId":      str(srcNodeId),
			"dstOwnerId":     str(dstOwnerId),
			"dstDatabaseId":  str(dstDatabaseId),
			"dstNodeId":      str(dstNodeId),
		}
		if srcPointId != None:
			newrec["srcPointId"] = str(srcPointId)
		if dstPointId != None:
			newrec["dstPointId"] = str(dstPointId)

		rec = self.db.find(newrec, limit=1)
		
		if rec == None: # Does not already exist		
			id = self.db.write(newrec)
			#trace("  new bind rec. id:" + str(id))
		else:
			id = rec["id"] #this is the binding id
			#trace("  existing bind rec. id:" + str(id))
		return id
	
	#TODO srcDatabaseId???
	#def unbind(self, srcOwnerId, srcNodeId, dstOwnerId, dstNodeId, dstPointId, dstDatabaseId):
	#	#trace("DB.unbind")
	#	raise ValueError("change API to require a srcDatabaseId")
	#	wanted = {
	#		"type":"BIND",
	#		"srcOwnerId":str(srcOwnerId),
	#		"srcNodeId":str(srcNodeId),
	#		"dstOwnerId":str(dstOwnerId),
	#		"dstDatabaseId":str(dstDatabaseId),
	#		"dstNodeId":str(dstNodeId),
	#		"dstPointId":str(dstPointId)
	#	}
	#
	#	rec = self.db.find(wanted, limit=1)
	#	if rec == None:
	#		raise ValueError("no BIND is active")
	#	id = rec["id"] # this is the binding id
	#	self.db.delete(id)
	#	#trace("UNBIND:" + str(id))


	def wakeup(self, ownerId, nodeId):
		# can only wakeup a local Node, so no databaseId needed
		#trace("DB.wakeup:" + str(ownerId) + " " + str(nodeId))
		#raise ValueError("HERE")
		self.wakeupRec(ownerId, nodeId)


	def wakeupRec(self, ownerId, nodeId):
		selector = {"type":"NODE", "ownerId":str(ownerId), "nodeId":str(nodeId)}
		rec = self.db.find(selector, limit=1)
		if rec == None:
			raise ValueError("Unknown node")
		rec["state"] = "AWAKE"
		id = rec["id"]
		self.db.overwrite(id, rec)			


	def sleep(self, ownerId, nodeId):
		# can only sleep a local Node, so no databaseId needed
		#trace("DB.sleep")
		self.sleepRec(ownerId, nodeId)


	def sleepRec(self, ownerId, nodeId):
		selector = {"type":"NODE", "ownerId":str(ownerId), "nodeId":str(nodeId)}
		rec = self.db.find(selector, limit=1)
		if rec == None:
			raise ValueError("Unknown node")
		rec["state"] = "ASLEEP"
		id = rec["id"]
		self.db.overwrite(id, rec)	


	# DELETION ---------------------------------------------------------

	#def deleteOwner(self, ownerId):
	#	"""delete an owner in the local database based on it'si index"""
	#	#if this is someone else, we just delete the reference
	#	#if this is us, we have to leave from our account also
	#	# exception if owner not known
	#	rec=self.db.find({"type":"OWNER", "ownerId":str(ownerId)}, limit=1)
	#	id = rec["id"]
	#	self.db.delete(id)


	#def deleteNode(self, ownerId, nodeId):
	#	"""delete a node in the local database based on it's index"""
	#	#can only delete a local point, so no databaseId needed
	#	#will have to delete all points first
	#	#note, is this index recyclable? Might be a db policy
	#	# exception if owner not known
	#	#exception if node not known
	#	rec = self.db.find({"type":"NODE", "ownerId":str(ownerId), "nodeId":str(nodeId)}, limit=1)
	#	id = rec["id"]
	#	self.db.delete(id)


	#def deletePoint(self, ownerId, nodeId, pointId):
	#	"""delete a point in the local database based on it's index"""
	#	# can only delete a local point, so no databaseId needed
	#	#note, is this index recyclable? Might be a db policy
	#	# exception if owner not known
	#	#exception if node not known
	#	#exception if point not known
	#	rec = self.db.find({"type":"POINT", "ownerId":str(ownerId), "nodeId":str(nodeId), "pointId":str(pointId)}, limit=1)
	#	id = rec["id"]
	#	self.db.delete(id)


	# DIAGNOSTICS -------------------------------------------------------------

	def dump(self):
		"""Show a diagnostic dump of the database, in human readable form"""
		self.showDatabase()
		self.showOwners()
		self.showNodes()
		self.showPoints()
		self.showBindings()


	def showDatabase(self):
		"""Show all name/number mappings, in human readable form"""
		dbRecs =  self.db.find({"type": "DATABASE"})
		for rec in dbRecs:
			databaseId = rec["databaseId"]
			print("DATABASE " + databaseId)


	def showOwners(self):
		ownerRecs = self.db.find({"type":"OWNER"})
		for rec in ownerRecs:
			ownerId    = rec["ownerId"]
			databaseId = rec["databaseId"]
			name       = rec["name"]
			print("OWNER (" + ownerId + " " + databaseId + ") => " + name)


	def showNodes(self):
		# {'databaseId': '99', 'name': 'garden', 'nodeId': '2', 'ownerId': '1', 'type': 'NODE', 'id': '4'}
		nodeRecs = self.db.find({"type":"NODE"})
		for rec in nodeRecs:
			ownerId     = rec["ownerId"]
			databaseId  = rec["databaseId"]
			nodeId      = rec["nodeId"]
			name        = rec["name"]
			print("NODE (" + ownerId + " " + databaseId + "." + nodeId + ") => " + name)


	def showPoints(self):
		pointRecs = self.db.find({"type":"POINT"})
		for rec in pointRecs:
			ownerId    = rec["ownerId"]
			databaseId = rec["databaseId"]
			nodeId     = rec["nodeId"]
			pointId    = rec["pointId"]
			pointType  = rec["pointType"]
			name       = rec["name"]
			print("POINT (" + ownerId + " " + databaseId + "." + nodeId + " " + pointId + ") => " + name + " " + pointType)


	def showBindings(self):
		"""Show all bind records, in human readable form"""
		# {'dstNodeId': '8', 'dstDatabaseId': '42', 'dstOwnerId': '1', 'srcPointId': '3', 'srcOwnerId': '1', 'bindType': 'ONE_TO_MANY', 'type': 'BIND', 'srcDatabaseId': '99', 'srcNodeId': '2', 'id': '10'}
		points   = self.getAllPointsMap()
		nodes    = self.getAllNodesMap()
		bindRecs = self.db.find({"type":"BIND"})

		for rec in bindRecs:
			srcOwnerId    = rec.get("srcOwnerId",    "?")
			srcDatabaseId = rec.get("srcDatabaseId", "?")
			srcNodeId     = rec.get("srcNodeId",     "?")
			srcPointId    = rec.get("srcPointId")
			dstOwnerId    = rec.get("dstOwnerId",    "?")
			dstDatabaseId = rec.get("dstDatabaseId", "?")
			dstNodeId     = rec.get("dstNodeId",     "?")
			dstPointId    = rec.get("dstPointId")

			src = (srcOwnerId, srcDatabaseId, srcNodeId, srcPointId)
			dst = (dstOwnerId, dstDatabaseId, dstNodeId, dstPointId)
			if srcPointId == None:
				srcName = nodes[(srcOwnerId, srcDatabaseId, srcNodeId)]
			else:
				srcName = points[src]
			if dstPointId == None:
				dstName = nodes[(dstOwnerId, dstDatabaseId, dstNodeId)]
			else:
				dstName = points[dst]
			bindType = rec["bindType"]

			if bindType == "ONE_TO_MANY":
				print("BIND " + str(src) + " --1:N--> " + str(dst))
				print("  " + srcName + " followed_by " + dstName)
			elif bindType == "MANY_TO_ONE":
				print("BIND " + str(src) + " --N:1--> " + str(dst))
				print("  " + srcName + " attached_to " + dstName)
			else:
				print("BIND " + str(src) + "-- " + str(bindType) +" -->" + str(dst))
				print("  " + srcName + "  ???? " + dstName)


# TEST HARNESS ---------------------------------------------------------

"""
def testIdDatabase():	
	idb = IdDatabase()
	idb.clear()
	idb.open()
	
	# OWNER
	ownerName = "thinkingbinaries.com"
	ownerId   = idb.newOwner(ownerName)
	#g = idb.getGlobalOwnerId(ownerId)
	#print("owner/globalId:" + str(g))
	
	
	# NODE
	nodeName = "sensor"
	nodeId = idb.newNode(ownerId, nodeName)
	#g = idb.getGlobalNodeId(ownerId, nodeId=nodeId)
	#print("node/globalId:" + str(g))
	#g = idb.getGlobalNodeId(ownerId, nodeName=nodeName)
	#print("node/globalId:" + str(g))
	
	
	# POINT/PRODUCER
	pointPName = "temperature"
	#pointPType = str(PRODUCER)
	#pointPId = idb.newPoint(ownerId, nodeId, pointPName, pointPType)
	#g = idb.getGlobalPointId(ownerId, nodeId, pointPId)
	#print("pointP/globalId:" + str(g))
	
	
	# POINT/CONSUMER
	pointCName = "catflap"
	#pointCType = str(CONSUMER)
	#pointCId = idb.newPoint(ownerId, nodeId, pointCName, pointCType)
	#g = idb.getGlobalPointId(ownerId, nodeId, pointCId)
	#print("pointC/globalId:" + str(g))
	
	# DELETE
	print(str(idb.db.indexlist))
	#idb.deletePoint(ownerId, nodeId, pointCId)
	
	print(str(idb.db.indexlist))
	#idb.deletePoint(ownerId, nodeId, pointPId)
	
	print(str(idb.db.indexlist))
	idb.deleteNode(ownerId, nodeId)

	print(str(idb.db.indexlist))
	idb.deleteOwner(ownerId)

	print(str(idb.db.indexlist))
"""


def dumpDatabase():
	import sys
	if len(sys.argv) < 2:
		dbPath = "test"
	else:
		dbPath = sys.argv[1]
	idb = IdDatabase(dbPath=dbPath)
	idb.open()
	idb.dump()
	idb.close()


if __name__ == "__main__":
	dumpDatabase()

# END
