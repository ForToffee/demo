GETTING STARTED WITH THE DEMO

1. WHAT IS THE DEMO

The demo is a tiny set of test scripts, that show that the system is working.
The intention of the demo is to show something sufficiently small and simple
that you can see what it does, in the hope that you will tinker with it
and then start to build your own demos. It is designed to be used in a
LAN-only lab environment, preferably on a set of Raspberry Pi computers
that are networked via a local router and that all have an IP address
already allocated (either statically or via DHCP).

The example has a house node, a garden node, and a boiler node.
The object of the demo is to keep the cat warm and happy.


2. CONFIGURING YOUR NETWORK STACK

Make sure you run the appropriate setup_ for your platform first.
This is so that your kernel is configured to route multicast messages onto
your LAN correctly, as the sandbox uses UDP multicast for all messaging.

You only have to do this again if you restart your machine.


3. RUNNING THE EXAMPLE IN THE LAN LAB

The garden advertises a temperature feed.
It also binds to the house catflap and controls it based on temperature.

The house advertises a catflap control.
The catflap can be configured in "locked", "let cat out only",
"let cat in only" or "let cat both ways".
The house also binds to the garden temperature feed and displays this.

The boiler binds to the garden temperature feed and displays it.
As the temperature rises and falls, it turns the boiler on and off.
It shares the boiler status as it changes as "on" or "off" messages.


cd Demo
./clean
(in a terminal window on one machine)
python house.py

(in a terminal window, on same pi or another pi)
python garden.py

(in a terminal window, on same pi or another pi)
python boiler.py


3. LOGGING COMMUNICATIONS

If you want to see a log of the LAN messages to the screen

cd Demo
cd IoticLabs
cd sandbox
python netcast.py log
(messages will scroll up on the screen as they happen)

If you want to "capture" a log to send me...

python netcast.py log > mylog.txt
CTRL-C to stop the logger
then email us the mylog.txt file


4. BREAKING OUT OF THE LAN SANDBOX

The demo is designed to work in a lab environment, i.e. on a LAN only.
If you want to link to another sandbox elsewhere on the internet, you can
use the gateway.py script - see the file runall for an example of how
you might configure this.


END.

