# garden.py  01/12/2014  D.J.Whale
#
# The garden advertises feeds for outside_temp and cat_detector
# it attaches to the house/catflap and controls it based on local temperature

# This is written using a lifecycle template
# There is only one node in this file (functions)
# but if you provide it as a class, the AppRunner can run multiple
# nodes from a single script

from IoticLabs.VirtualSpace import Node, Point, AppRunner


# CONFIGURATION --------------------------------------------------------

L_GARDEN_NODE  = "garden"       # tester/garden
L_OUTSIDE_TEMP = "outside_temp" # tester/garden/outside_temp
L_CAT_DETECTOR = "cat_detector" # tester/garden/cat_detector

R_HOUSE_NODE   = "house"        # tester/house
R_CATFLAP      = "catflap"      # tester/house/catflap


# STATE ----------------------------------------------------------------

l_garden       = None
l_outside_temp = None
l_cat_detector = None
r_catflap      = None

last_catflap   = "unknown"
temp           = 18
tempdir        = +1 # rising
cat            = False
lastcat        = False


# INIT ----------------------------------------------------------------

def create():
	"""Create virtual representations of all our local stuff"""
	global l_garden
	
	l_garden = Node.create(L_GARDEN_NODE)
	t = l_garden.createPoint(L_OUTSIDE_TEMP) # FEED
	t.advertise() # FEED
	
	d = l_garden.createPoint(L_CAT_DETECTOR) # FEED
	d.advertise() # FEED
	return l_garden
	
	
def bind():
	"""Find and knit to anything static remote that we need in order to work"""

	c = l_garden.find(R_CATFLAP, nodeName=R_HOUSE_NODE) # CONTROL
	c.attach()


# RESTORE --------------------------------------------------------------

def restore():
	"""Restore connectivity on start or restart, route to callbacks"""
	global l_garden, l_outside_temp, l_cat_detector, r_catflap
	
	l_garden = Node.restore(L_GARDEN_NODE)

	l_outside_temp = l_garden.routePoint(Point.LOCAL, L_OUTSIDE_TEMP)
	l_cat_detector = l_garden.routePoint(Point.LOCAL, L_CAT_DETECTOR)
	r_catflap      = l_garden.routePoint(Point.REMOTE, R_CATFLAP, nodeName=R_HOUSE_NODE)

	return l_garden
		

# RUN ------------------------------------------------------------------

def wakeup():
	"""The node starts functioning"""
	l_garden.wakeup()


def loop():
	"""The body of the node code"""
	global cat, lastcat, temp, tempdir, last_catflap

	# simulate: 50% probability of a cat entering the garden
	cat = not cat
	if cat != lastcat:
		l_cat_detector.share(cat)
		lastcat = cat

	# simulate: temp rises then falls
	temp = temp + tempdir
	if temp > 30:
		tempdir = -1
	elif temp < 10:
		tempdir = +1
	l_outside_temp.share(temp)
	
	# behaviour: cat flap directions change based on temperature
	if temp > 20: # HOT
		if last_catflap != "out":
			r_catflap.ask("cat_out_only")
			last_catflap = "out"
			
	elif temp < 18:
		if last_catflap != "in":
			r_catflap.ask("cat_in_only")
			last_catflap = "in"

	l_garden.loop()
	
	
def sleep():
	"""The node is stopping"""
	l_garden.sleep()
	
	
# MAIN -----------------------------------------------------------------
# Use this to run the garden node standalone
	
if __name__ == "__main__":
	import sys
	me = (L_GARDEN_NODE, sys.modules[__name__])	
	AppRunner.run(me)

# END
