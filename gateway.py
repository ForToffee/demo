# gateway.py  18/03/2015  D.J.Whale
#
# A simple multi hub-based gateway.
# Provides a method for linking multiple IOTic Labs together.
# This version only supports one hub (1 put port, 1 get port)
# and one LAN at present.


#TODO LIST --------------------------------------------------------------------

# multi LAN instances - it would be possible to listen to multiple LAN's (i.e.
# multicast address and port). So we need an architecture that would
# (a) allow multiple listeners and (b) allow them to be configured,
# presumably we just pass the linkPath to them for that.
# This will need a list of LAN's to implement this.
# If we handle multiple LAN's in a single gateway, we will have to
# instantiate an interface for each LAN here, and also have a separate
# tx queue for each of those LANs (We have a single TX queue at present)


# 3) multi PUT ports, multi GET ports
# want to have a list of PUT ports to publish LAN messages to.
# want to have a list of GET ports to read remote network messages from
# will require more care on naming and knitting, we have a single shared
# FilePut/Get HUB at the moment, which is a bit contrived.


import time
import urllib2
import httplib
import Queue

from IoticLabs.Listener import MetaListener, DataListener
from IoticLabs.sandbox.Address import StrAddress
import IoticLabs.sandbox.Link as Link
import IoticLabs.Config as cfg



# CONFIGURATION ---------------------------------------------------------------

LAN_QUEUE_MAX       = cfg("lan_queue_max", default=20)
HUB_QUEUE_MAX       = cfg("hub_queue_max", default=20)


def trace(msg):
    print(str(msg))

def warning(msg):
    print("warning:" + str(msg))


# RoutingTable ----------------------------------------------------------------------

class InterfaceItem():
    def __init__(self, parent, owner):
        self.parent = parent
        self.owner = owner


    def getMyName(self):
        return self.owner


    def getOwnerFor(self, id):
        owner = self.parent.getOwnerFor(id)
        return owner


    def claim(self, id):
        try:
            owner = self.parent.getOwnerFor(id)
            # already owned by someone, might be me
            return owner # This is who owns it
        except KeyError:
            # not yet owned, so we will claim it
            self.parent.setOwnerFor(id, self.owner)
            return self.owner # I have just claimed it


class RoutingTable():
    def __init__(self, filename="routes.db"):
        self.routes   = {}
        self.filename = filename


    def createInterface(self, owner):
        return InterfaceItem(self, owner)


    def setOwnerFor(self, id, owner):
        """Set the owner for this id"""
        trace("# RoutingTable.setOwner:" + owner + "=" + str(id))
        self.routes[id] = owner


    def getOwnerFor(self, id):
        """Get the name of interface who owns this id"""
        return self.routes[id]


    def iOwnThisId(self, owner, id):
        """Do I own this id?"""
        return (self.routes[id] == owner)


    def save(self):
        """Save all routes to the file"""
        pass # TODO


    def load(self):
        """Reload all routes from the file"""
        pass # TODO


    def commit(self):
        """If any changes made to routes, commit to file"""
        pass # TODO


    def refresh(self):
        """Reload routes from file, only if date/time stamp has changed"""
        pass # TODO


    def getReverseRoutes(self):
        """Turn id->owner into owner->[ids]"""
        owners = {}
        for id in self.routes:
            owner = self.routes[id]
            if not owners.has_key(owner):
                owners[owner] = [id]
            else:
                (owners[owner]).append(id)
        return owners


    @staticmethod
    def listToCSV(items):
        """Generate a CSV from a list of items"""
        csv = ""
        for i in items:
            if csv != "":
                csv += ","
            csv += str(i)
        return csv


    def dump(self):
        """Dump all routes to stdout"""
        # group them as owner->[ids], so reverse the ordering first
        owners = self.getReverseRoutes()
        for o in owners:
            ids = self.listToCSV(owners[o])
            print(str(o) + ":" + ids)


# MESSAGE ---------------------------------------------------------------------
#
# An abstraction of a message (Meta or Data message) complete with
# addresses, and a simple wire encoding/decoding protocol that we can use with
# the hub to exchange messages.
#
# A message is encoded as a colon separated string.
# newlines are not allowed
# binary characters in data are not allowed
# srcAddr:dstAddr:msgtype:data
# (0 33.1 2):(7 99.2 1):meta.state.ind:AWAKE

class Message():
    def __init__(self, info, data):
        self.info = info
        self.data = data

    def __repr__(self):
        return "Message(info=" + str(self.info) + " data=" + str(self.data)  + ")"


    @staticmethod
    def decodeFrom(s):
        """Factory to create a Message() from an encoded string"""
        #trace("decodeFrom:" + str(s))
        src, dst, msgtype, data = s.split(":", 3)
        srcAddr                 = StrAddress.createFrom(src)
        dstAddr                 = StrAddress.createFrom(dst)
        info                    = Link.Info(msgtype, srcAddr, dstAddr)
        return Message(info, data)


    def getSrcAddr(self):
        return self.info.src


    def getSrcDatabaseId(self):
        return self.info.src.databaseId


    def isMeta(self):
        """Is this a Meta message?"""
        if self.info != None and self.info.msg != None and self.info.msg.startswith("meta"):
            return True
        return False


    def isData(self):
        """Is this a Data message?"""
        if self.info != None and self.info.msg != None and self.info.msg.startswith("data"):
            return True
        return False


    def getEncoded(self):
        """Return an encoded string representation of the Message()"""
        result = str(self.info.src) + ":" + str(self.info.dst) + ":" + str(self.info.msg) + ":" + str(self.data)
        return result


# LAN ----------------------------------------------------------------------
#TODO can LAN() and HUB() inherit from the same NetInterface() base class?
#It will then be easy to pass references to these into the routing table manager.
#or we could choose to store parts of the routing table that belong to
#each network agent within the agent itself, and the routing table then just
#has a list of network agents?


#TODO want to be able to have multiple LAN's in future
#so will have to have an interfaceId to disambiguate in routing tables
#NOTE: The interfaceId is inside myroutes.getMyOwnerName()

class LAN():
    def __init__(self, myroutes, rxqueue, metaLinkPath=None, dataLinkPath=None, routeLocal=False):
        self.myroutes   = myroutes
        self.rxqueue    = rxqueue
        self.routeLocal = routeLocal # Don't route local messages out of the LAN

        class MyMetaListener(MetaListener):
            def __init__(self, parent, linkPath):
                MetaListener.__init__(self, linkPath)
                self.parent = parent

            def handleMeta(self, info, data):
                self.parent.handleIncomingMessage(info, data, Message(info, data))

        class MyDataListener(DataListener):
            def __init__(self, parent, linkPath):
                DataListener.__init__(self, linkPath)
                self.parent = parent

            def handleData(self, info, data):
                self.parent.handleIncomingMessage(info, data, Message(info, data))

        self.meta = MyMetaListener(self, metaLinkPath)
        self.data = MyDataListener(self, dataLinkPath)

        if metaLinkPath == None:
            self.metaSender = Link.MulticastNetConnection()
        else:
            self.metaSender = Link.MulticastNetConnection(
                Link.MulticastNetConnection.getAddress(metaLinkPath),
                Link.MulticastNetConnection.getPort(metaLinkPath)
            )

        if dataLinkPath == None:
            self.dataSender = Link.MulticastNetConnection()
        else:
            self.dataSender = Link.MulticastNetConnection(
                Link.MulticastNetConnection.getAddress(dataLinkPath),
                Link.MulticastNetConnection.getPort(dataLinkPath)
            )


    def handleIncomingMessage(self, info, data, msg):
        #trace(str(info))
        #trace(str(data))

        srcDatabaseId = info.src.databaseId
        dstDatabaseId = info.dst.databaseId

        # Keep the local routing table up to date with addresses owned by this LAN
        if srcDatabaseId != None:
            # src addresses received on our own LAN will always belong to us
            # so claim them if we don't already own them
            intf = self.myroutes.claim(srcDatabaseId)
            if intf != self.myroutes.getMyName():
                warning("Multiple interfaces own databaseId:" + str(srcDatabaseId))

        # Route it externally, only if necessary
        if self.shallIRoute(srcDatabaseId, dstDatabaseId):
            self.rxqueue.put(msg)


    def shallIRoute(self, srcDatabaseId, dstDatabaseId):
        """Make a policy decision whether to route this message or not"""
        if self.routeLocal:
            # Always route local messages to external ports
            return True # Yes, do route it externally

        else:
            if dstDatabaseId == None:
                # We have no idea whether we own it or not, so this must be "broadcast"
                # To the widest audience.
                return True # Yes, do route it externally

            # dstDatabaseId!=None, so it's destined for a specific Node
            dstIntfName  = self.myroutes.getOwnerFor(dstDatabaseId)
            myIntfName   = self.myroutes.getMyName()
            if dstIntfName == None: # we don't know which interface to route it via
                warning("No route for databaseId:" + str(dstDatabaseId))
                return True # Yes, route it anyway just in case
            else:
                if myIntfName != dstIntfName: # It's not on our LAN
                    trace("# Sending msg due to dst not on our LAN:" + str(dstDatabaseId))
                    return True # Yes, do route it externally
                else:
                    trace("# Squashing msg due to dst on our LAN:" + str(dstDatabaseId))
                    return False # No, don't route it, it's on our LAN

        return False # No, don't route it externally


    def send(self, msg):
        """Send a MetaMessage or a DataMessage via correct link"""
        trace("# LAN.send:" + str(msg))

        # Route via appropriate link. These might be the same, but we route
        # anyway, in case the architecture has been knitted with separate links.

        # Fudge the payload encoding done by Meta() and Data() classes
        def reformat(msg):
            r = str(msg.info.msg) + " " + str(msg.info.src) + " " + str(msg.info.dst)
            if msg.data != None:
                r += " " + str(msg.data)
            return r

        if msg.isMeta():
            self.metaSender.write(reformat(msg))
        elif msg.isData():
            self.dataSender.write(reformat(msg))
        else:
            raise ValueError("Unknown message type:" + str(type(msg)))


    def loop(self):
        self.meta.loop()
        self.data.loop()


# PUT/GET Ports (generic) ---------------------------------------------------------------

class PUTPort():
    def __init__(self):
        pass


    def put(self, message):
        """write a message to the PUT port"""
        trace("put:" + str(message))


    def reset(self):
        """Reset PUT port to initial empty state (no message)"""
        pass



class GETPort():
    def __init__(self):
        pass


    def get(self):
        """Get an individual incoming message from the GET port"""
        # Returns None if nothing waiting to be got.
        return "{received message}"
        # Or return None if nothing waiting


    def reset(self):
        """Reset GET port to initial empty state (no message)"""
        pass



class PUTQueue(PUTPort):
    def __init__(self):
        PUTPort.__init__(self)
        self.outqueue = Queue.Queue()


    def put(self, message):
        """add another message to the outgoing queue"""
        trace("# put:" + str(message))
        self.outqueue.put(message)


    def commit(self):
        """Send all queued outgoing messages"""
        trace("# commit")

    def reset(self):
        pass


    def purge(self, upToPosition):
        pass


class GETQueue(GETPort):
    def __init__(self):
        GETPort.__init__(self)
        self.inqueue = Queue.Queue()


    def sync(self):
        """synchronise next-read counter up to current position"""
        pass # TODO


    def poll(self, maxmsgs=10):
        """Receive a package formax(maxmsgs) in size"""
        trace("#get.poll(" + str(maxmsgs) + ")")
        return 0 # no messages received


    def getInCount(self):
        """Get number of unprocessed messages read from the HUB GET port"""
        return len(self.inqueue)


    def get(self):
        """Get an individual incoming message from the inqueue"""
        try:
            m = self.inqueue.get(block=False)
            return m
        except Queue.Empty:
            return None


    def reset(self):
        """reset next-read counter to start of stream"""
        pass # TODO



# File PUT/GET ports ----------------------------------------------------------

class FilePUT(PUTQueue):
    def __init__(self, filename="PUT.txt"):
        PUTQueue.__init__(self)
        self.lastseek = 0
        self.filename = filename


    def reset(self):
        """Clear the file of any existing data"""
        f = open(self.filename, "w")
        f.close()
        self.lastseek = 0


    def purge(self, upToPosition):
        pass # TODO


    def commit(self, maxmsgs=10):
        f = open(self.filename, "a+")
        sent = 0

        while sent < maxmsgs:
            try:
                m = self.outqueue.get(block=False)
                if type(m) == Message:
                    m = m.getEncoded()
                f.write(str(m) + "\n")
                sent += 1
            except Queue.Empty:
                break
        f.close()
        return sent


class FileGET(GETQueue):
    def __init__(self, filename="GET.txt"):
        GETQueue.__init__(self)
        self.lastseek = 0
        self.filename = filename


    def reset(self):
        """Clear the file of any existing data"""
        self.lastseek = 0


    def poll(self, maxmsgs=10): # read n messages in one go?
        f = open(self.filename, "r")
        f.seek(self.lastseek)
        trace("poll seek to:" + str(self.lastseek))
        received = 0

        while received < maxmsgs:
            line = f.readline()
            if len(line) == 0:
                #trace("EOF reached")
                break

            line = line.strip() # remove newline
            try:
                line = Message.decodeFrom(line)
            except:
                warning("Can't decode message:" + str(line))
                # go ahead regardless, useful for testing
            self.inqueue.put(line)
            received += 1

        self.lastseek = f.tell()
        trace("poll saves seek:" + str(self.lastseek))
        f.close()
        return received


    def getLastSeekPos(self):
        return self.lastseek



# HTTP PUT/GET ports/queues ---------------------------------------------------

class HTTPPUT(PUTQueue):
    def __init__(self, url):
        PUTQueue.__init__(self)
        self.url = url
        from urlparse import urlparse
        o = urlparse(self.url)
        if o.scheme != 'http':
            raise ValueError("Must be http, got:" + str(o.scheme))
        self.server = o.netloc
        self.path   = o.path


    def reset(self):
        pass #TODO tell server to clear any stored messages
        trace("# httpput:reset")
        c = httplib.HTTPConnection(self.server)
        headers = {} # put token in here
        body = ""
        c.request("DELE", self.path, body, headers)

        response = c.getresponse()
        status = response.status
        reason = response.reason
        responseBody = response.read()
        trace(str(status) + " " + str(reason) + " " + str(responseBody))

        response.close()
        c.close()


    def purge(self, upToPosition):
        pass #TODO tell server to clear stored messages up to this index
        trace("# httpput:purge")


    def commit(self, maxmsgs=10):
        trace("# httpput.commit:" + str(maxmsgs))
        sent = 0

        body = ""
        while sent < maxmsgs:
            try:
                m = self.outqueue.get(block=False)
                m = m.getEncoded()
                body += str(m) + "\n"
                sent += 1
            except Queue.Empty:
                break

        if sent > 0:
            c = httplib.HTTPConnection(self.server)
            headers = {} # put token in here
            c.request("POST", self.path, body, headers)

            response = c.getresponse()
            status = response.status
            reason = response.reason
            responseBody = response.read()

            trace(str(status) + " " + str(reason) + " " + str(responseBody))

            response.close()
            c.close()

        return sent


# Uses a temporary client-side method of lastseek
# will eventually use a server assisted method via php params
# But this method allows us to attach to any http stream/file
# although it is terribly inefficient with big files.

class HTTPGET(GETQueue):
    def __init__(self, url):
        GETQueue.__init__(self)
        self.url = url
        self.lastseek = 0


    def sync(self):
        self.lastseek = self.countLines()


    def countLines(self):
        response = urllib2.urlopen(self.url)
        lines = 0
        while True:
            l = response.readline()
            if l == None:
                break
            lines += 1
        response.close()
        return lines


    def reset(self):
        self.lastseek = 0


    def poll(self, maxmsgs=10):
        trace("httpget.poll:" + str(maxmsgs))
        try:
            response = urllib2.urlopen(self.url)
        except urllib2.HTTPError:
            warning("GET port not yet created")
            return 0

        received = 0

        # seek to lastseek
        if self.lastseek != 0:
            for s in range(self.lastseek):
                l = response.readline()

        # Read in up to maxmsgs messages into the queue
        while received < maxmsgs:
            line = response.readline()
            if len(line) == 0:
                #trace("EOF reached")
                break

            line = line.strip() # remove newline
            try:
                line = Message.decodeFrom(line)
            except:
                warning("Can't decode message:" + str(line))
                # go ahead regardless, useful for testing
            self.inqueue.put(line)
            received += 1

        response.close()
        self.lastseek += received
        return received


# TIMER -----------------------------------------------------------------------
# Set time horizons, sets a flag if it is time for processing
# uses time.time with simple maths to be resilient to cpu overloads
# but probably also tells you if you missed a timeslot by a lot
import time

class Timer:
    def __init__(self, periodms, offsetms = 0, async=True):
        self.periodms = periodms
        self.offsetms = offsetms
        self.async    = async
        self.resync()


    def resync(self, advance=None):
        if advance == None: # async
            self.nexttime = time.time() + self.periodms + self.offsetms
        else: # sync
            self.nexttime = self.nexttime + advance


    def isReady(self):
        now  = time.time()
        diff = now - self.nexttime

        if diff < 0:
            # timer is still running
            #trace("remaining-ms:" + str(diff))
            return False # NOT ready

        else:
            # timer has expired
            late = diff
            if late > 1:
                warning("Timer lateby-ms:" + str(late))

            if self.async:
                # asynchronous timer restarts the timer on each detected tick,
                # without trying to adjust for being late.
                # Late timers will cause long term drift
                # i.e. min time between fires is always at least 'periodms'
                self.resync()

            else: # synchronous
                # synchronous timer always refers to an original origin time
                # late timers will mean the next timer will fire sooner
                # i.e. min time between fires can be less than 'periodms'
                self.resync(self.periodms)

            return True # IS ready


# MAIN PROGRAM ================================================================

# STARTUP ---------------------------------------------------------------------

# The routing table that holds all routes
routes = RoutingTable()


# CONFIGURATION OF HUB

#putPort = FilePUT(cfg("put_filename", "PUT.txt"))
putPort = HTTPPUT(cfg("put_url"))
putPort.reset()

#getPort = FileGET(cfg("get_filename", "GET.txt"))
#non server assisted GET at moment, so do a real get of the raw data file.
getPort = HTTPGET(cfg("get_url"))
getPort.reset()


# An object that manages a list of routes on this HUB interface only
# Really this is the GET/PUT port of a specific HUB
put_routes = routes.createInterface("PUT")
get_routes = routes.createInterface("GET")


# read in last known hubin sequence number processed
#hub_poller.read()


# CONFIGURATION OF LAN

# An object that manages a list of routes on this LAN interface only
lan_routes = routes.createInterface("LAN")

# messages on the LAN are automatically routed to it's HUB putPort.
# If routeLocal=True, all local messages will be routed externally.
#TODO: Still testing
lan = LAN(lan_routes, putPort,
          routeLocal   = cfg("routeLocal", default=False),
          metaLinkPath = cfg("lanaddr",    default=None),
          dataLinkPath = cfg("lanaddr",    default=None))

# Queue for messages that need to be transmitted back to the LAN
# (i.e. messages that come from the HUB getPort)
lan_tx_queue = Queue.Queue()


# TIMERS/SCHEDULING
# Run the whole thing slowly at the moment while testing
# offset each type of message transfer so it is easier to see how it is working.
lanrx_timer  = Timer(cfg("timer_base",default=4), cfg("timer_lanrx_offset",  default=0))
hubput_timer = Timer(cfg("timer_base",default=4), cfg("timer_hubput_offset", default=1))
hubget_timer = Timer(cfg("timer_base",default=4), cfg("timer_hubget_offset", default=2))
lantx_timer  = Timer(cfg("timer_base",default=4), cfg("timer_lantx_offset",  default=3))


# RUN -------------------------------------------------------------------------

def processLANRxMessages():
    """Process reading of LAN messages"""

    if lanrx_timer.isReady():
        trace("# try LAN rx loop")
        lan.loop()


def processLANTxMessages():
    """Process sending of HUB messages to LAN"""

    if lantx_timer.isReady():
        trace("# try LAN tx")
        #TODO might have a send limit to prevent LAN flooding.
        sent = 0
        while True:
            try:
                msg = lan_tx_queue.get(block=False)
                trace("# Sending to LAN:" + str(msg))
                lan.send(msg)
                sent += 1
            except Queue.Empty:
                trace("# Sent to LAN:" + str(sent))
                break


def processHUBPUT():
    """Process regular writing to the PUT port on the HUB"""

    #TODO might add a feature to send early if queue is really full
    if hubput_timer.isReady():
        trace("# try hubput")
        putPort.commit()


def processHUBGET():
    """Process regular polling of the GET port from the HUB"""
    global hub_get_queue

    if hubget_timer.isReady():
        trace("# try hubget")

        num = getPort.poll()
        if num != 0:
            trace("# Messages read from hub:" + str(num))
            for i in range(num):
                msg = getPort.get()
                #trace("ProcessingMsg:" + str(msg))
                databaseId = msg.getSrcDatabaseId()
                if databaseId != None:
                    owner = get_routes.claim(msg.getSrcDatabaseId())
                    #TODO if the owner is the LAN, don't send it back, it's a cycling message
                    if owner == "LAN":
                        trace("# Squashed reflected message for dbId:" + str(databaseId))
                    else:
                        # If it's from something at the other end of the hub, we need to retransmit locally
                        trace("# Routing HUB message to LAN for dbId:" + str(databaseId))
                        lan_tx_queue.put(msg)

def main():
    trace("Gateway started")

    #try:
    while True:
        # Slow down the loop, while we are testing
        time.sleep(1)
        routes.dump()

        processLANRxMessages()
        processHUBPUT()
        processHUBGET()
        processLANTxMessages()


    # STOP ------------------------------------------------------------------------

    #finally:
        # try to cache dbid's and horizon numbers
        #try:
        #    lan_idcache.commit()
        #except:
        #    warning("Failed to commit lan_idcache")

        #try:
        #    hub_idcache.commit()
        #except:
        #    warning("Failed to commit hub_idcache")

        #try:
        #    hub_poller.commit()
        #except:
        #    warning("Failed to commit hub_poller")

        #trace("finished")

# TESTING =====================================================================

def test():
    """Do a loopback test via a HTTPPUT port, back in via a HTTPGET port"""
    URL = "http://www.thinkingbinaries.com/iothub/test1/"
    PUT_SIZE = 10
    GET_SIZE = 10

    # File based queue
    #FILE = "test.txt"
    #getQueue = FileGET(FILE)
    #putQueue = FilePUT(FILE)
    #putQueue.reset()

    # HTTP based queue
    # Using (dumb) GET mode at the moment
    getQueue = HTTPGET(URL + "data.txt")
    # Using server side assisted PUT mode
    putQueue = HTTPPUT(URL)
    putQueue.reset()

    # Generic loopback tester
    count = 1
    while True:
        time.sleep(1)

        # Queue and send a batch of messages
        for i in range(PUT_SIZE):
            m = "msg:" + str(count)
            putQueue.put(m)
            count += 1
        putQueue.commit(PUT_SIZE)

        # get and dump some queued messages
        if getQueue.poll(GET_SIZE) != 0:
            while True:
                m = getQueue.get()
                if m == None:
                    break
                print("got:" + str(m))


# MAIN PROGRAM ================================================================

main()
#test()

# END
