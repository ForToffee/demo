# Search.py  11/08/2014  D.J.Whale
#
# Kick off a search to get the entities list database back

import IoticLabs.JoinIOT as IOT
from config import *
import time

MY_NAME = MY_COMPUTER + "_Search"

IOT.joinAs(MY_NAME)

g = IOT.getGUID("demo2")
print("GUID:" + g)

g2 = IOT.getGUID("demo")
print("GUID:" + g2)

IOT.loop()

IOT.leave()

# END
