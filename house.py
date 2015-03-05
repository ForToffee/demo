# house.py  01/12/2014  D.J.Whale
#
# The house follows the garden outside_temp to monitor it.
# It also has a catflap that can be remotely controlled.

# Written using the (simpler) IOT wrapper
# You can only have one owner and one node per script using the IOT wrapper.

import IoticLabs.IOT as IOT


# CONFIGURATION --------------------------------------------------------

L_HOUSE_NODE   = "house"            # thinkingbinaries/house
L_CATFLAP      = "catflap"          # thinkingbinaries/house/catflap

R_GARDEN_NODE  = "garden"           # thinkingbinaries/garden
R_OUTSIDE_TEMP = "outside_temp"     # thinkingbinaries/garden/outside_temp


# STATE -----------------------------------------------------------------------

l_catflap      = None
r_outside_temp = None

catflap_mode   = "locked"


# CALLBACKS -------------------------------------------------------------------

def catflap_ask(info, data):
	global catflap_mode
	print("house: catflap_ask:" + str(data))
	catflap_mode = data


def temp_update(info, data):
	print("house: temp_update:" + str(data))


# MAIN ------------------------------------------------------------------------

if IOT.init(L_HOUSE_NODE):
	# CREATE LOCAL POINTS
	t = IOT.createPoint(L_CATFLAP) # CONTROL
	t.advertise() # CONTROL

	# BIND TO REMOTE POINTS
	t = IOT.find(R_OUTSIDE_TEMP, nodeName=R_GARDEN_NODE) # FEED
	t.follow()

# RESTORE LOCAL AND REMOTE POINTS
IOT.restore()
l_catflap      = IOT.routePoint(IOT.LOCAL, L_CATFLAP, receive=catflap_ask) #ask
r_outside_temp = IOT.routePoint(IOT.REMOTE, R_OUTSIDE_TEMP, nodeName=R_GARDEN_NODE, receive=temp_update) # update

# WAKEUP
IOT.wakeup()

# RUN
import time

try:
	while True:
		time.sleep(1)
		IOT.loop()

finally:
	print("*" * 80)
	print("exception in loop, trying to sleep")
	print("*" * 80)

	IOT.sleep()

# END

