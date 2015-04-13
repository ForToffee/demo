# sandbox.Address.py  D.J.Whale  November 2014
#
# This defines how addresses are encoded and parsed "on the wire"
#
# This is not the same as VirtualSpace.Address, but much of the code
# is copied from there. Eventually it will be replaced with a
# BinaryAddress for binary based transports

def trace(msg):
	print(str(msg))


def toStr(value):
	"""Read a value, store it as None or a str"""
	if value == None:
		return None
	return str(value)
	

class StrAddress():
	"""An Address has a databaseId, ownerId, nodeId and pointId"""
		
	def __init__(self, ownerId=None, nodeId=None, pointId=None, databaseId=None, nodeAddr=None):
		self.set(ownerId, nodeId, pointId, databaseId, nodeAddr)


	def __repr__(self):
		result = "("

		if self.ownerId == None:
			return result + ")"

		result += str(self.ownerId)

		if self.nodeId == None:
			return result + ")"
		result += " "

		if self.databaseId != None:
			result += str(self.databaseId) + "."
		else:
			result += "?."
			trace("warning: databaseId is not set")
		result += str(self.nodeId)

		if self.pointId == None:
			return result + ")"

		result += " " + str(self.pointId) + ")"
		return result


	def set(self, ownerId=None, nodeId=None, pointId=None, databaseId=None, nodeAddr=None):
		# Trap missing databaseId setting
		if nodeId != None:
			if databaseId == None:
				raise ValueError("databaseId must be set if nodeId is set")
		elif nodeAddr != None:
			if nodeAddr[1] != None and nodeAddr[0] == None:
				raise ValueError("nodeAddr must have a databaseId")

		self.ownerId    = toStr(ownerId)
		self.nodeId     = toStr(nodeId)
		self.pointId    = toStr(pointId)
		self.databaseId = toStr(databaseId)
		if nodeAddr != None:
			self.databaseId = toStr(nodeAddr[0])
			self.nodeId     = toStr(nodeAddr[1])
		

	def clear(self):
		self.databaseId = None
		self.ownerId    = None
		self.nodeId     = None
		self.pointId    = None


	@staticmethod
	def parse(s):
		if s == None:
			raise ValueError("Cannot parse None")
		if type(s) != str:
			trace("s=" + str(s))
			raise ValueError("Expected a string to parse, got:" + str(type(s)))
			
		# ()
		# (o)
		# (o d.n)
		# (o d.n p)
		if s == None or len(s) < 2 :   # ()
			raise ValueError("Invalid empty address")
		if s[0] != '(' or s[-1] != ')':
			raise ValueError("Address not bracketed: '" + s + "'")
			
		s = s[1:-1] # strip brackets		
		
		if len(s) == 0:
			return (None, None, None, None) #databaseId, ownerId, nodeId, pointId

		parts = s.split(" ") # split out address parts
		#trace("  parts:" + str(parts))

		databaseId = None
		ownerId    = None
		nodeId     = None
		pointId    = None

		# first is ownerId
		if len(parts) >= 1:
			ownerId = parts[0]

		# second is databaseId.nodeId
		if len(parts) >= 2:
			dn = parts[1]
			databaseId, nodeId = dn.split(".", 1)

		# third is pointId
		if len(parts) >= 3:
			pointId = parts[2]

		if len(parts) > 3:
			raise ValueError("More than 3 parts found in address:" + str(parts))
			
		return (databaseId, ownerId, nodeId, pointId)


	@staticmethod
	def createFrom(s):
		a = StrAddress()
		a.getFrom(s)
		return a


	def getFrom(self, s):
		self.databaseId, self.ownerId, self.nodeId, self.pointId = self.parse(s)


	@staticmethod #DRY: repeated in Address
	def match(filterAddr, compareAddr):
		"""Do two addresses match, with wildcards?"""
		#This is a static method, so it can be applied to anything
		#that works like an Address, regardless of it's class
		#trace("Addr.match: filter:" + str(filterAddr) + " against:" + str(compareAddr))

		if filterAddr.ownerId == None:
			#trace("ownerId matches all")
			return True # matches all ownerIds

		if str(filterAddr.ownerId) != str(compareAddr.ownerId):
			#trace("ownerId mismatch")
			#trace(str(type(filterAddr.ownerId)))
			#trace(str(type(compareAddr.ownerId)))
			return False

		if filterAddr.nodeId == None:
			#trace("ownerId+nodeId matches all")
			return True # matches all nodeId's for this ownerId

		if filterAddr.databaseId == None:
			raise ValueError("filter address has an empty databaseId")
		if compareAddr.databaseId == None:
			raise ValueError("compare address has an empty databaseId")

		if str(filterAddr.databaseId) != str(compareAddr.databaseId):
			#trace("databaseId mismatch")
			return False

		if str(filterAddr.nodeId) != str(compareAddr.nodeId):
			#trace("nodeId mismatch")
			return False

		if filterAddr.pointId == None:
			#trace("ownerId+nodeId+pointId matches all")
			return True # matches all pointId's for this ownerId+nodeId

		if str(filterAddr.pointId) != str(compareAddr.pointId):
			#trace("pointId mismatch")
			return False

		#trace("match")
		return True # everything matches


# Create EMPTY as a useful constant, but must do it after StrAddress is defined.
StrAddress.EMPTY = StrAddress()


"""
def testAddress():
	# CREATE
	a = Address()
	print(str(a))
	
	# SET
	a.set()
	print(str(a))
	a.set(1)
	print(str(a))
	a.set(1, 2)
	print(str(a))
	a.set(1, 2, 3)
	print(str(a))
	a.set(None, 2, 3)
	print(str(a))
	
	# GET
	print(str(a.get()))
	
	# CLEAR
	a.clear()
	print(str(a))

	# parse
	#print(str(Address.parse(""))) # empty Address
	#print(str(Address.parse("freddsfasdfs"))) # not bracketed 
	print(str(Address.parse("(1 2 3)")))
	print(str(Address.parse("(- - -)")))
	print(str(Address.parse("(1 - -)")))
	print(str(Address.parse("(1 2 -)")))
	print(str(Address.parse("(- - 3)")))
	
	# getFrom
	a.getFrom("(1 2 3)")
	print(str(a))
	
	# setOwnerId/getOwnerId
	a.set()
	a.setOwnerId(1)
	print(str(a))
	print(a.getOwnerId())
	
	# setNodeId/getOwnerId
	a.set()
	a.setNodeId(2)
	print(str(a))
	print(a.getNodeId())
	
	# setPointId/getPointId
	a.set()
	a.setPointId(3)
	print(str(a))
	print(a.getPointId())
	
	# MATCH
	a.set(1, 2, 3)
	print(a.match(1, 2, 3))
	print(a.match(1, None, None))
	print(a.match(2, None, None))
	print(a.match(None, None, 3))
	print(a.match(None, None, 4))
	print(a.match(1, 2, None))
"""