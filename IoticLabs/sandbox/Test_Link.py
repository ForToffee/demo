import Link as l
import time
import sys

FILENAME = "test"
ID = sys.argv[1]
		
count = 0
while True:
	time.sleep(0.5)
	print("tick")
	msgout = u"test:" + ID + str(count)
	print("out:" + msgout)
	l.write(msgout)
	count += 1
	
	time.sleep(0.1)
	msgin = l.read()
	msgin = msgin.strip()
	print("in:" + msgin)
	
# END
