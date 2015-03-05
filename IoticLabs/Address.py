# IoticLabs.Address.py  D.J.Whale  November 2014
#
# This is a useful grouping of address components
#
# This is an Address without any specific representation.
# If you want an Address with a specific representation for on the wire use,
# use sandbox/Address.py/StrAddress() instead
#
# Inside generic code, addresses should always be used without a representation
# to help keep the code independent of any particular wire format. We will
# probably change the wire format to binary eventually, and don't want that
# to impact on the rest of the system design.

# Note, be careful of internal representation differences between this Address
# and the sandbox address - specifically with match() if you compare between
# two different address types. At the moment they are identical, but be careful
# if considering changing internal formats.

def trace(msg):
	print(str(msg))


def toStr(value):
	"""Read a value, store it as None or a str"""
	if value == None:
		return None
	return str(value)


class Address():
	"""An Address has an ownerId, nodeId and pointId"""

	def __init__(self, ownerId = None, nodeId = None, pointId = None, databaseId=None, nodeAddr=None):
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
			result += self.databaseId + "."
		else:
			result += "?."
			trace("warning: Missing databaseId in address)")
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

		self.databaseId = toStr(databaseId)
		self.ownerId    = toStr(ownerId)
		self.nodeId     = toStr(nodeId)
		self.pointId    = toStr(pointId)
		if nodeAddr != None:
			self.databaseId = toStr(nodeAddr[0])
			self.nodeId     = toStr(nodeAddr[1])

		
	def clear(self):
		self.databaseId = None
		self.ownerId    = None
		self.nodeId     = None
		self.pointId    = None


	@staticmethod #DRY: Repeated in sandbox/StrAddress
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

# Create EMPTY for convenience, and put it inside the class Address()
# Must do this here as Address is now defined.
Address.EMPTY = Address()


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
"""

# END
