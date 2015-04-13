# netcast.py  21/11/2014  D.J.Whale
#
# Multicast networking via UDP sockets

import socket
import struct
import time
import Multicast

# For test harness only
TEST_ADDRESS   = Multicast.DEFAULT_ADDRESS
TEST_PORT      = Multicast.DEFAULT_PORT

# But conveniently, it's the same as the address of our IOT, for logging purposes,
# so that if you start the logger with no parameters, you get something sensible
# still.

DEFAULT_IOT_ADDRESS = Multicast.DEFAULT_ADDRESS
DEFAULT_IOT_PORT    = Multicast.DEFAULT_PORT

LOCALHOST = "127.0.0.1"
ANYIP     = "0.0.0.0"


# SENDER ---------------------------------------------------------------
# inspiraton from:
#   http://pymotw.com/2/socket/multicast.html

class Sender():
	"""Send messages to a nominated multicast UDP address and port number"""


	def __init__(self, address, port, ttl=1, name="Unknown"):
		# TTL0 = local node only
		# TTL1 = local LAN only
		self.address           = address
		self.port              = port
		self.multicast_group   = (address, port)
		self.sock              = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.name              = name
		#ttlstruct = struct.pack('b', ttl)
		#self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttlstruct)
		
		self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)


	def send(self, message):
		sent = self.sock.sendto(message, self.multicast_group)
			
	def finished(self):
		self.sock.close()
		self.sock = None
    
    
# RECEIVER ------------------------------------------------------------- 
# With help from:
#   http://stackoverflow.com/questions/1694144/can-two-applications-listen-to-the-same-port
#   https://mail.python.org/pipermail/python-list/1999-May/014273.html


class Receiver():
	"""Receive multicast messages from a nominated UDP multicast address
	   and port number"""
	   
	def __init__(self, address, port, name="Unknown"):
		self.address = address
		self.port    = port
		self.name    = name
		
		self.multicast_group = address
		# might need group, port where multiple NICs in use		
		self.server_address  = ('', port)
		
		# Create the socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		
		# set socket options so that other processes can also bind here
		# for Ubuntu Linux
		#self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)	
		# for Mac OSX
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

		# Bind to the server address
		self.sock.bind(self.server_address)

		# After the regular socket is created and bound to a port, it can be 
		# added to the multicast group by using setsockopt() to change the 
		# IP_ADD_MEMBERSHIP option. The option value is the 8-byte packed 
		# representation of the multicast group address followed by the network 
		# interface on which the server should listen for the traffic, 
		# identified by its IP address. In this case, the receiver listens on 
		# all interfaces using INADDR_ANY.

		# Tell the operating system to add the socket to the multicast 
		# group, on all interfaces.
		self.group          = socket.inet_aton(self.multicast_group)
		#self.rxip           = socket.inet_aton(address)   
		self.rxip           = socket.inet_aton("0.0.0.0")
		#The ip_mreq structure 
		#(taken from /usr/include/linux/in.h) has the following members:
		#struct ip_mreq
		#{
		#		struct in_addr imr_multiaddr;   /* IP multicast address of group */
		#		struct in_addr imr_interface;   /* local IP address of interface */
		#};
		# https://docs.python.org/2/library/struct.html

		mreq       = struct.pack('4s4s', self.group, self.rxip)
		try:
			self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
		except socket.error:
			print("")
			print("*" * 80)
			print("error: no physical network, no multicast route")
			print("If you are on localhost only, try...")
			print("sudo route add -net 224.0.0.0 netmask 224.0.0.0 lo")
			print("*" * 80)
			print("")
			raise ValueError("Can't connect to network")
			
	##TODO this does not cope with line breaks.
	#typically one message per payload so it might just come out in wash
	def receive(self, maxlen=1024):
		"""A blocking receive for data"""
		# Note, this is not line at a time, could be multiple lines
		# including partial lines.
		data, address = self.sock.recvfrom(maxlen)
		#DEBUG
		#print("UDP." + self.name + ".rx " + str(data))
		return data, address
		
	def peek(self):
		try:
			data, address = self.sock.recvfrom(1, socket.MSG_PEEK + socket.MSG_DONTWAIT)
		except socket.error as e:
			errno = e.errno
			if errno == 11 or errno == 35: # WOULDBLOCK or TEMPUNAVAIL
				return False
			else:
				print("unexpected error:" + str(e))
				raise e
		return True

	def finished(self):
		self.sock.close()
		self.sock = None
		
	
# TEST HARNESS----------------------------------------------------------

def testSender(number):
	rate=1
	s = Sender(TEST_ADDRESS, TEST_PORT)
	c = 0
	while True:
		time.sleep(rate)
		s.send(str(number) + ":hello world:" + str(c))
		c += 1
	
	
def testReceiver(number):
	r = Receiver(TEST_ADDRESS, TEST_PORT)
	while True:
		address, data = r.receive()
		print(str(number) + ":" + str(address) + ":" + str(data))
		

import thread # python2
		
		
def testThreads(tx=1, rx=1):	
	idx = 1

	for r in range(rx):
		thread.start_new_thread(testReceiver, ("rx(" + str(idx) + ")",))
		idx += 1

	for t in range(tx):
		thread.start_new_thread(testSender, ("tx(" + str(idx) + ")",))
		idx += 1

	while True:
		time.sleep(1)
		
		
def testCooperative(tx=1, rx=1):
	receivers = []
	transmitters = []
	for r in range(rx):
		receivers.append(Receiver(TEST_ADDRESS, TEST_PORT))
	for t in range(tx):
		transmitters.append(Sender(TEST_ADDRESS, TEST_PORT))
		
	seq = 0
	while True:
		# Transmit messages
		seq += 1
		txno = 0
		for t in transmitters:
			msg = "tx(" + str(txno) + ") " + str(seq)
			print(msg)
			t.send(msg)
			txno += 1
		time.sleep(1)
			
		# Wait for all messages to arrive at all receivers
		c = 0
		while c < len(receivers):
			rxno = 0
			for r in receivers:
				if r.peek():
					msg = r.receive()
					print("rx(" + str(rxno) + ") received:" + str(msg))
					c += 1
				rxno += 1
				
		
def logger(address, port):
	r = Receiver(address, port)
	while True:
		data, addr = r.receive()
		print(str(addr) + ":" + str(data))
		
		
if __name__ == "__main__":
	import sys
	cmd = sys.argv[1]
	if cmd == "sender":
		testSender(0)
		
	elif cmd == "receiver":
		testReceiver(0)
		
	elif cmd == "threads":
		testThreads(tx=2, rx=2)
		
	elif cmd == "coop":
		testCooperative(tx=4, rx=4)
		
	elif cmd == "log":
		#TODO use Config here
		address = DEFAULT_IOT_ADDRESS
		port    = DEFAULT_IOT_PORT
		if len(sys.argv) > 2:
			address = sys.argv[2]
			if len(sys.argv) > 3:
				port = int(sys.argv[3])

		logger(address, port)
	else:
		print("Unknown mode, try 'sender' or 'receiver'")
		
# END
