# __main__.py 01/12/2014  D.J.Whale

from IoticLabs.VirtualSpace import AppRunner

import garden
import house
import boiler

# Must now start garden as a normal process
APPS = [
#    ("garden", garden),
    ("house",  house),
    ("boiler", boiler)
]

print("*" * 80)
print("*" * 80)

AppRunner.runAll(APPS, rate=0.5, debug=False)

	
# END
