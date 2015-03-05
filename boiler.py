# boiler.py  01/12/2014  D.J.Whale
#
# The boiler follows the garden outside_temp
# It turns the boiler on and off based on the outside temp
# It published a feed of it's present ON state
# It also does a local loopback of ON, to prove this works

# This is written using a lifecycle template
# There is only one node in this file (functions)
# but if you provide it as a class, the AppRunner can run multiple
# nodes from a single script

from IoticLabs.VirtualSpace import Node, Point, AppRunner


# CONFIGURATION --------------------------------------------------------

L_BOILER_NODE  = "boiler"          # thinkingbinaries/boiler
L_ON           = "on"              # thinkingbinaries/boiler/on

R_GARDEN_NODE  = "garden"          # thinkingbinaries/garden
R_OUTSIDE_TEMP = "outside_temp"    # thinkingbinaries/garden/outside_temp


# STATE ----------------------------------------------------------------

l_boiler       = None
l_on           = None
r_outside_temp = None
loopback_on    = None

on             = False


# INIT ----------------------------------------------------------------

def create():
	"""Create virtual representations of all our local stuff"""
	global l_boiler
	
	l_boiler = Node.create(L_BOILER_NODE)
	b = l_boiler.createPoint(L_ON) # FEED
	b.advertise() # FEED
	return l_boiler
		

def bind():
	"""Find and knit to anything static remote that we need in order to work"""
	t = l_boiler.find(R_OUTSIDE_TEMP, nodeName=R_GARDEN_NODE) # FEED
	t.follow()

	t = l_boiler.find(L_ON, nodeName=L_BOILER_NODE) # MY FEED
	t.follow()


# RESTORE --------------------------------------------------------------

def restore():
	"""Restore connectivity on start or restart, route to callbacks"""
	global l_boiler, r_outside_temp, l_on, loopback_on
	
	l_boiler       = Node.restore(L_BOILER_NODE)
	l_on           = l_boiler.routePoint(Point.LOCAL, L_ON)
	r_outside_temp = l_boiler.routePoint(Point.REMOTE, R_OUTSIDE_TEMP, nodeName=R_GARDEN_NODE, receive=temp_update) #update
	loopback_on    = l_boiler.routePoint(Point.REMOTE, L_ON, nodeName=L_BOILER_NODE, receive=loopback_on) #update
	return l_boiler
	
	
# CALLBACKS ------------------------------------------------------------------

def loopback_on(info, data):
	print("boiler: loopback_on:" + str(data))


def temp_update(info, data):
	global on
	
	print("boiler: temp_update:" + str(data))
	temp = int(data)
	
	# control boiler based on temp, with hysterisis
	if temp < 12: # Cold outside
		if not on:
			print("boiler: Turn on")
			on = True
			l_on.share(str(on))
		
	elif temp > 15: # Hot outside
		if on:
			print("boiler: Turn off")
			on = False
			l_on.share(str(on))


# RUN -------------------------------------------------------------------------

def wakeup():
	"""The node starts functioning"""
	l_boiler.wakeup()

	
def loop():
	"""The body of the node code"""
	l_boiler.loop()

		
def sleep():
	"""The node is stopping"""
	l_boiler.sleep()
	
	
# MAIN -----------------------------------------------------------------
# Use this to run the boiler node standalone
	
if __name__ == "__main__":
	import sys
	me = (L_BOILER_NODE, sys.modules[__name__])
	AppRunner.run(me)
	
# END
