# how to enable kernel based local multicast on a node
# you will need to do this before any of the examples work

# mac
#sudo route -nv add -net 224.0.0.0 -netmask 224.0.0.0 -interface lo0

# make sure if you have multiple machines, that they have a unique
# IP address, and that you can ping one from the other, e.g.

ping 192.168.1.3

# linux (including Raspberry Pi)
# Do this every time you boot your Pi, to make sure that multicast
# messages work correctly.

sudo route add -net 224.0.0.0 -netmask 224.0.0.0 -interface lo0
sudo route add -net 224.0.0.0 -netmask 224.0.0.0 -interface eth0

# windows (not tried yet)


# how to run the example

cd Demo
./clean
(in a terminal window on one machine)
python house.py
databaseId: 42

(in a terminal window, on same pi or another pi)
python garden.py
databaseId: 99

(in a terminal window, on same pi or another pi)
python boiler.py
(if it asks you for a databaseId, enter a unique id)
(if you are running on a shared machine, it might choose an existing
database, or it might give you a choice)




If you want to see a log of the messages

cd Demo
cd IoticLabs
cd sandbox
python netcast.py log
(messages will scroll up on the screen as they happen)

If you want to "capture" a log to send me...

python netcast.py log > mylog.txt
CTRL-C to stop the logger
then email me the mylog.txt file

