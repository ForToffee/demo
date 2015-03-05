# IOT.py
#
# This is a convenience wrapper around the static methods in VirtualSpace
# so that you can say:
#   import VirtualSpace.IOT as IOT

# The whole of VirtualSpace is inside the IOT namespace,
# so the using module could use IOT.Owner, IOT.Point and IOT.Node if it wants to.


from VirtualSpace import *
import random


# CONSTANTS -------------------------------------------------------------------
# These are for convenience, so they are IOT.GENERIC rather than IOT.Point.GENERIC

GENERIC     = Point.GENERIC
ONE_TO_MANY = Point.ONE_TO_MANY
MANY_TO_ONE = Point.MANY_TO_ONE
LOCAL       = Point.LOCAL
REMOTE      = Point.REMOTE


# DEFAULTS --------------------------------------------------------------------

DEFAULT_OWNER_NAME = "Owner"
DEFAULT_NODE_NAME  = "Node"

#TODO turn this into a socket reference (ip:port or name:port)
#so that we can use different links, and a single config parameter
DEFAULT_LINK_ADDRESS = "224.3.29.71"
DEFAULT_LINK_PORT    = 10000



# SINGLETON STATE -------------------------------------------------------------

myOwnerName = None
myOwner     = None
myNodeName  = None
myNode      = None


def init(nodeName, ownerName=None, dbPath=None, linkPath=None):
    global myOwnerName, myOwner
    global myNodeName, myNode

    # Set some sensible defaults, if caller does not provide them
    if nodeName == None:
        nodeName = DEFAULT_NODE_NAME + "#" + str(random.randint(0,65535))
    if linkPath == None:
        linkPath = DEFAULT_LINK_ADDRESS + ":" + str(DEFAULT_LINK_PORT)


    myOwner = Owner.use(ownerName, linkPath=linkPath, dbPath=dbPath)
    myOwnerName = myOwner.ownerName

    state = myOwner.getStateForNode(nodeName)
    myNodeName  = nodeName

    if state == None:  # not yet created
        myNode = Node.create(nodeName, owner=myOwner)
        myNode.loop()
        return True # we just Initialised
    return False # we didn't need to init the Node


def createPoint(pointName, pointType=None):
    return myNode.createPoint(pointName, pointType=pointType)


def find(pointName, ownerName=None, nodeName=None, pointType=None):
    return myNode.find(pointName, ownerName, nodeName, pointType=pointType)


def restore():
    global myNode

    myNode = Node.restore(myNodeName)
    myNode.loop()
    return myNode


def routePoint(pointType, pointName, nodeName=None, receive=None):
    return myNode.routePoint(pointType, pointName, nodeName=nodeName, receive=receive)


def wakeup():
    myNode.wakeup()


def loop():
    myNode.loop()


def sleep():
    myNode.sleep()

# END


