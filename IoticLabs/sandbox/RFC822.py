# RFC822.py (c) 2013 @whaleygeek
#
# Based on open source code from http://blog.whaleygeek.co.uk
#
# See this for "efficient ways to read files", as the file object is iterable
#
# http://stackoverflow.com/questions/8009882/how-to-read-large-file-line-by-line-in-python

import os
import os.path
import time


# CONFIGURATION ---------------------------------------------------------------

def trace(msg):
	print("RFC822:" + str(msg))


#-----------------------------------------------------------------------
# A file-based mutex lock, that can be used to enforce atomic transactions.

class Lock():
	"""A filing system based lock object abstraction"""

	def __init__(self, name):
		self.name = name
		self.f    = None


	def __repr__(self):
		return "Lock(" + str(self.name) + ")"


	@staticmethod
	def _myPID():
		"""Get the Process ID of this process"""
		return str(os.getpid())


	def deleteOld(self):
		"""Delete an old lock file"""
		#trace("deleteOld")
		if not self.check():
			return False # No file, nothing done
		try:
			os.remove(self.name)
		except:
			return False # Could not remove file
		return True # File existed and removed, apparently


	def check(self):
		"""Check if the lock is in use or not"""
		#trace("check")
		# True if lock file is present
		# False if lock file is absent
		return os.path.isfile(self.name)


	def whoHasIt(self):
		"""Get the PID of the process that has the lock"""
		if self.f != None:
			return "mine" # I have it locked

		try:
			f = open(self.name)
			owner = f.readline()
			f.close()
			return owner
		except IOError:
			return None # There is no lock file


	def claim(self):
		"""Try to claim the lock, return False if not claimed"""
		#trace("claim")
		try:
			self.f = open(self.name, "w")
		except:
			raise ValueError("Already locked by:" + str(self.name))

		self.f.write(self._myPID() + "\n")
		self.f.flush()
		# Leave file open, so it is locked


	def wait(self, ratems=0.1, times=None):
		"""Poll a lock every so often, until it is free, then claim it"""
		#trace("wait")
		while True:
			try:
				self.claim()
				return # got it!
			except:
				time.sleep(rate)
				if times != None:
					times -= 1
					if times == 0:
						raise ValueError("Timeout waiting for lock")


	def release(self):
		"""Release the lock"""
		#trace("release")
		if self.f == None:
			raise ValueError("Cannot release, not locked by me")
		self.f.close()
		self.f = None
		try:
			os.remove(self.name)
		except OSError:
			pass
		return True # We released it


# SIMPLE TEST

def testLock():
	l = Lock("mylock")
	pid = l._myPID()

	while True:
		time.sleep(0.25)
		l.wait()
		print(str(pid) + ":GOT IT")
		l.release()


#-----------------------------------------------------------------------
# A Writer that writes in RFC822 format.
# This is a raw writer that just handles 1 record at a time
# It always writes to the end of the file

class RFC822Writer:
	def __init__(self, name):
		self.name = name
		self.file = None

	def start(self):
		"""Start writing to a file, at the end of the file"""
		self.file = open(self.name, "at")
		#trace("RFC822Writer: start:" + str(self.file))

	def write(self, map, keyName=None):
		"""Write one record to the file"""
		# if keyName is provided, that is always written first
		if keyName != None:
			keyValue = map[keyName]
			del map[keyName]
			self.file.write(keyName + ": " + str(keyValue) + "\n")
			 
		for key in map:
			self.file.write(key + ": " + str(map[key]) + "\n")
		self.file.write("\n")
		self.file.flush()
		
	def writeMeta(self, key, value, data):
		"""Add metadata to the file"""
		# This is done by a file format violation (no colon on key)
		# but assumes there is no colon in "data"
		self.file.write(key + ": " + value + "\n")
		self.file.write(data + "\n")
		self.file.write("\n")
		self.file.flush()
		
	def getPos(self):
		"""Get the next position to write to in the file, always at end"""
		return self.file.tell()
		
	def setPos(self, newPos):
		"""Update the next write position, normaly by advancing it"""
		self.file.seek(newPos)

	def finished(self):
		"""close the file when all done"""
		if self.file != None:
			self.file.close()
			self.file = None


# SIMPLE TESTER

def testWriter():
	w = RFC822Writer("test.txt")
	m = {"id":1, "name":"david", "age":45}
	w.start()
	w.write(m)

	m["age"] = 46
	w.write(m)

	m["age"] = 47
	w.write(m, keyName="id")
	w.writeMeta("id", "1", "DELETE")
	w.finished()
 
 
#-----------------------------------------------------------------------
# A Reader that reads RFC822 formatted records

class RFC822Reader:
	def __init__(self, name):
		self.name = name
		self.file = None
		self.pos = 0
		self.lastSize = 0
	
	def exists(self):
		"""check if the file exists"""
		try:
			self.file = open(self.name, "rt")
			self.file.close()
			return True
		except:
			return False

	def start(self):
		"""start reading from the start of the file"""
		#trace("RFC822Reader: start:" + str(self.file))
				
		#if self.file == None:
		#	self.file = open(self.name, "rt")
		#else:
		#	self.file.seek(0)
		self.pos = 0
		self.lastSize = self.getSize()

	def setPos(self, position):
		"""Set the read position to this file offset"""
		# File offset probably returned by readIndex		
		#self.file.seek(position)
		self.pos = position
		
	def getPos(self):
		"""Get the present read position in file"""
		#return self.file.tell()
		return self.pos

	def skip(self, n=1):
		self.file = open(self.name, "rt")
		self.file.setpos(self.pos)
		self._skip(n)
		self.pos = self.file.tell()
		self.file.close()
		
	def _skip(self, n=1):
		"""Skip a specified number of records"""
		if (n == None or n <= 0):
			return None # nonsense, do nothing
		if (n == 0):
			return 0 # none skipped, but we did it

		count = 0
		while True:
			# Read one line at a time, to prevent tell() damage
			line = self.file.readline()
			if line == "":
				break # EOF
			#trace(line)
			if (line == "\n"): # blank line means end of record
				#trace("EOF")
				count += 1
				if (count >= n):
					return count # we skipped this number of whole records

		# if we get here, it is EOF
		return None # means we didn't achieve desired result, now at EOF

	def read(self):
		self.file = open(self.name, "rt")
		#trace("read start: seek to:" + str(self.pos))
		self.file.seek(self.pos)
		rec = self._read()
		self.pos = self.file.tell()
		#trace("read end: at pos:" + str(self.pos))
		self.file.close()
		return rec
		
	def _read(self):
		"""Read the record at the present position"""
		map = {}
		while True:
			# read one line at a time, to prevent tell() damage
			line = self.file.readline()
			#trace("readline:" + str(line))
			if line == "":
				break # EOF
			if (line == "\n"):
				return map # end of record
			else:
				item = line.split(":", 1)
				try:
					key = item[0]
				except IndexError:
					#self.finished() # prevent re-reads without re-open
					return None # malformed record
				try:
					value = item[1]
					value = value.rstrip('\n').strip()
				except IndexError:
					value = None
				map[key] = value

		# if we get here it is EOF
		return None # EOF before whole record retrieved

	def getLastSize(self):
		return self.lastSize

	def getSize(self):
		"""Get the size of the underlying file, in bytes"""
		# This is useful to work out if it has grown since last use
		self.file = open(self.name, "rt")
		SEEK_END = 2
		self.file.seek(0, SEEK_END)
		pos = self.file.tell()
		self.file.close()
		return pos
		
	def sizeChanged(self, newSize):
		self.lastSize = newSize
		
	#TODO deprecate???
	def finished(self):
		"""Finished, close the file"""
		if (self.file != None):
			self.file.close()
			self.file = None


# SIMPLE TESTER

def testReader():
	r = RFC822Reader("test.txt")
	r.start()

	r.skip(1)
	item = r.read()
	for k in item:
		print(k + "=" + item[k])

	r.setPos(0)
	item = r.read()
	for k in item:
		print(k + "=" + item[k])

	r.finished()


# INDEX ----------------------------------------------------------------

class Index():
	# indexlist is []->key (deleted indexes are None)
	# indexmap is key->pos
	
	def __init__(self):
		self.clear()
		
	def __repr__(self):
		return "list:" + str(self.indexlist) + " map:" + str(self.indexmap)

	def clear(self):
		self.indexmap = {}
		self.indexlist = []
		
	def keyUsed(self, keyValue):
		return self.indexmap.has_key(keyValue)
		
	def getList(self):
		return self.indexlist
					
	def add(self, keyValue, pos):
		"""Add a key value to the fast lookup index"""
		if keyValue == None:
			raise ValueError("Can't add keyValue=None")
			
		keyValue = str(keyValue)
		if self.indexmap.has_key(keyValue):
			raise ValueError("Already in index:" + keyValue)
		self.indexmap[keyValue] = pos
		self.indexlist.append(keyValue)

	def write(self, keyValue, pos):
		"""Write to index regardless of if key present or not"""
		keyValue = str(keyValue)
		if self.indexmap.has_key(keyValue):
			# already exists, so update
			self.update(keyValue, pos)
		else:
			# does not exist, so create
			self.add(keyValue, pos)
		
	def update(self, keyValue, pos):
		"""Update an existing index entry"""
		keyValue = str(keyValue)
		if not self.indexmap.has_key(keyValue):
			raise ValueError("Index does not have key:" + keyValue)
		self.indexmap[keyValue] = pos
		#no need to update indexlist here, because it already maps to the key
		
	def remove(self, keyValue):
		"""Remove an item from the index"""
		keyValue = str(keyValue)
		if not self.indexmap.has_key(keyValue):
			raise ValueError("Index does not have key:" + keyValue)
		del self.indexmap[keyValue]
		#TODO search indexlist for keyValue
		#TODO mark that entry as None

	def read(self, keyValue):
		"""Get the file position for the last written value of keyName=keyValue"""
		keyValue = str(keyValue)
		if not self.indexmap.has_key(keyValue):
			raise ValueError("Index does not have key:" + keyValue)
		return self.indexmap[keyValue]
			
	def readAt(self, idx):
		"""Get the file position for last written value for rec(idx)"""
		if idx > len(self.indexlist):
			raise ValueError("Index pos out of range:" + str(idx))
		key = self.indexlist[idx]
		if key == None:
			raise ValueError("Rec at index is deleted:" + str(idx))
		rec = self.readIndex(key)
		return rec
		
	def getActiveCount(self):
		"""count the number of active records in the file"""	
		return len(self.indexmap)
		
	def getUsedCount(self):
		return len(self.indexlist)


# SIMPLE TESTER

def testIndex():
	r = RFC822Database()

	r.addToIndex("one", 10)
	print(r.index)

	#r.addToIndex("one", 20) # exception

	r.updateIndex("one", 30)
	print(r.index)

	r.writeIndex("one", 40)
	print(r.index)

	#r.removeFromIndex("two") # exception

	r.removeFromIndex("one")
	print(r.index)

	#pos = r.readIndex("one") # exception

	r.writeIndex("present", 33)
	pos = r.readIndex("present")
	print(pos)


#-----------------------------------------------------------------------
# A database has an index, which if in memory implies this database
# has a single writer, if the index is on disk, the database is
# multi writer. It's always multi reader though.

class RFC822Database():
	META_KEY  = "_meta"
	DELETED   = "DELETED"
	LOCK_NAME = "db.lock"
	
	def __init__(self, name="database", keyName="id"):
		self.dbName = name
		self.keyName = keyName
		self.reader = None
		self.writer = None
		self.index = Index()
		self.lock = Lock(self.LOCK_NAME)
		
	def __repr__(self):
		return "list:" + str(self.index)


	def create(self):
		"""Create a new database, but leave it closed"""
		import os
		if os.path.isfile(self.dbName):
			raise ValueError("Cannot create database, already exists:" + str(self.dbName))

		# create the raw file
		f = open(self.dbName, "w")
		f.close()


	def clear(self):
		"""Create/Clear the database"""
		self.close()
		f = open(self.dbName, "w")
		f.close()
		self.index.clear()
		self.open(read=True, write=True)
		
	def open(self, read=False, write=False):
		"""Open a file for read and/or write mode"""
		# Note, must explicitly create, not assumed create
		import os
		if not os.path.isfile(self.dbName):
			raise ValueError("Database does not exist, auto create disabled:" + str(self.dbName))
		#TODO read/write mode not honoured yet
		self.writer = RFC822Writer(self.dbName)
		self.reader = RFC822Reader(self.dbName)
		self.writer.start()
		self.reader.start()
		self.rebuildIndex()
		
	def close(self):
		"""close a file once finished"""
		#TODO DEPRECATE
		if self.reader != None:
			self.reader.finished()
		#TODO DEPRECATE
		if self.writer != None:
			self.writer.finished()
		self.index.clear()

	def getNextKey(self):
		"""Get the next key to allocate when autonumbering"""
		# Because IndexList has holes marked with None for deleted recs,
		# this does not recycle id numbers
		self.refreshIndex()		
		return self.index.getUsedCount()
						
	def refreshIndex(self):
		"""check the file and apply any new transactions to the index"""
		# We have to keep writer.pos updated too, so it always appends
		# to the correct position
		oldSize = self.reader.getLastSize()
		newSize = self.reader.getSize()
		if oldSize != newSize:
			self.deltaIndex(oldSize, newSize)
			self.reader.sizeChanged(newSize)
			# we don't maintain the writer pointer here
			# it only needs updating prior to a write operation
			# which is more efficient.
				
	def deltaIndex(self, oldSize, newSize):
		"""Rebuild the index from the last known rebuild point"""
		# work out the last known length
		# process all records from there to end, updating index
		self.reader.setPos(oldSize)
		pos = oldSize
		while pos != None and pos <= newSize:
			#trace("INDEXING REC")
			pos = self.indexNextRec()
			#trace("pos now:" + str(pos))
			
	def rebuildIndex(self):
		"""Rebuild the internal fast lookup index from scratch"""
		# This does a full file read from start to finish
		self.index.clear()
		# The index is only in memory at the moment
		self.reader.start()
		while self.indexNextRec() != None:
			pass 			
			
	def indexNextRec(self):
		"""Index the next rec at the reader pos"""
		# i.e. read the next record from reader pos and process it
		pos = self.reader.getPos()
		rec = self.reader.read()
		if rec == None:
			return None # EOF
		key = rec[self.keyName]
		meta = None
		try:
			meta = rec[self.META_KEY]
		except KeyError:
			pass
		if meta != None and meta == self.DELETED:
			self.index.delete(key)
		else:
			self.index.write(key, pos)
		pos = self.reader.getPos()
		return pos			
		
	def getCount(self):
		"""count the number of active records in the file"""
		return self.index.getCount()
				
	def read(self, keyValue):
		"""Get the record that matches this key"""
		self.refreshIndex()
			
		keyValue = str(keyValue)
		#trace("read:" + keyValue)
		#trace("indexmap:" + str(self.indexmap))
		
		pos = self.index.read(keyValue)
		#trace(" pos:" + str(pos))
		self.reader.setPos(pos)
		rec = self.reader.read()
		#trace(" rec:" + str(rec))
		return rec
				
	def write(self, record, morekeys=None):
		"""write a new record to the file"""
		self.refreshIndex()
		if self.writer != None:
			self.writer.setPos(self.reader.getSize())
			
		if not record.has_key(self.keyName):
			keyValue = self.getNextKey()
			record[self.keyName] = keyValue
		else:
			keyValue = record[self.keyName]
			if self.index.keyUsed(keyValue):
				raise ValueError("key already in index:" + str(keyValue))

		#We can also optionally set other fields to the allocated key value
		#This is useful, as we can't support compound keys, it's a bit of a bodge
		#but it works good enough.
		if morekeys != None:
			for k in morekeys:
				record[k] = keyValue
				#trace("adding key:" + str(k) + "=" + str(keyValue))

		pos = self.writer.getPos()
		#trace(" writer says pos is:" + str(pos))
		self.lock.wait()
		self.writer.write(record)
		self.lock.release()
		self.index.add(keyValue, pos)
		return keyValue

	def update(self, keyvalue, record):
		"""Update only those fields in record"""
		#does a read of the record, then overlays record on top
		raise ValueError("DB.update not yet written")
		#should have replaced all calls with overwrite()
		#this is here just in case we missed any
		
	def overwrite(self, keyValue, record):
		"""change the values in an existing record where key matches"""
		self.refreshIndex()
		if self.writer != None:
			self.writer.setPos(self.reader.getSize())			
				
		keyValue = str(keyValue)
		if not self.index.keyUsed(keyValue):
			raise ValueError("Key not in index:" + str(keyValue))
		record[self.keyName] = keyValue
		pos = self.writer.getPos()
		self.lock.wait()
		self.writer.write(record)
		self.lock.release()
		self.index.update(keyValue, pos)
		pos = self.writer.getPos()
		
	def delete(self, keyValue):
		"""delete an existing record where the key matches"""
		self.refreshIndex()
		if self.writer != None:
			self.writer.setPos(self.reader.getSize())	
					
		if not self.index.hasKey(keyValue):
			raise ValueError("Key does not exist in index:" + str(keyValue))
		keyValue = str(keyValue)
		self.lock.wait()
		self.writer.writeMeta(self.keyName, keyValue, self.DELETED)
		self.lock.release()
		self.index.delete(keyValue)

	@staticmethod
	def match(criteria, rec):
		"""and-match all criteria against rec"""
		#trace("match:" + str(criteria) + " " + str(rec))
		for k in criteria:
			v = criteria[k]
			if not rec.has_key(k):
				return False
			if rec[k] != v:
				return False
		return True
				
	def find(self, criteria={}, limit=None):
		"""find a set of records based on criteria and limits"""		
		#trace("find:" + str(criteria))
		self.refreshIndex()
					
		results = []
		count = 0
		#trace(self.indexlist)
		for key in self.index.getList():
			#trace(" key:" + key)
			if key != None: 
				# not deleted
				rec = self.read(key)
				if rec == None:
					raise ValueError("Key did not lead to a record:" + str(key))
				#trace("  rec:" + str(rec))
				if self.match(criteria, rec):
					results.append(rec)
					count += 1
					if limit != None and count >= limit:
						break
		
		#trace(" results:" + str(results))		
		if limit != None and limit == 1:
			if len(results) > 0:
				return results[0]
			else:
				return None
		return results	

	def records(self):
		"""An interator for all records in the file"""
		raise ValueError("not yet implemented")
		#iterate all records by reading
		#really need to build and return an iter??
		#an iter will return the next record on each call
		#for i in db.records(): do(i)  

	# temporary debug only
	def getSize(self):
		if self.reader != None:
			return self.reader.getSize()
		else:
			return None


# SIMPLE TESTER

def testRFC822Database():
	# CREATE/CLEAR
	db = RFC822Database("test.db", "id")
	db.clear()
	
	# COUNT
	db.open(read=True)
	c = db.getCount()
	print("count:" + str(c))
	db.close()
	
	db.open(write=True)
	rec = {"name":"david"}
	key = db.write(rec)
	print("firstkey:" + key)
	db.close()
	
	db.open(read=True)
	c = db.getCount()
	print("count:" + str(c))
	db.close()
	
	# READ
	db.open(read=True, write=True)
	rec = db.read(0)
	print("read(1):" + str(rec))

	# UPDATE
	rec = {"name":"fred"}
	key = db.write(rec)
	print("key:" + key)
	
	db.update("1", {"name":"harry"})
	rec = db.read("1") 
	print("rec:" + str(rec))
	
	# DELETE
	db.delete("1")
	print("map:" + str(db.indexmap))
	print("list:" + str(db.indexlist))

	# FIND
	db.write({"name":"sid",   "age": "46"})
	db.write({"name":"james", "age": "46"})
	db.write({"name":"bert",  "age": "33"})
	
	rs = db.find({}, limit=None)
	print("find all, no limit:" + str(rs))

	r = db.find({}, limit=1)
	print("find all, limit 1:" + str(r))
	
	r = db.find({"name": "fred"}, limit=1)
	print("find fred:" + str(r))
	
	r = db.find({"name": "james"}, limit=1)
	print("find james:" + str(r))
	
	rs = db.find({"age": "46"})
	print("find all age 46:" + str(rs))
	
	db.close()
	
	
def testRFC822Database2():
	# Two live instances connected to same physical file
	# check that in memory indexes are kept up to date across instances
	
	db1 = RFC822Database("test2.db", "id")
	db1.clear()
	db2 = RFC822Database("test2.db", "id")
	
	db1.open()
	db2.open()

	s1 = db1.getSize()
	s2 = db2.getSize()
	print("s1:" + str(s1) + " s2:" + str(s2))
	
	db1.write({"name":"david"})
	db1.write({"name":"gail"})

	s1 = db1.getSize()
	s2 = db2.getSize()
	print("s1:" + str(s1) + " s2:" + str(s2))

	c1 = db1.getCount()
	c2 = db2.getCount()
	print("count1:" + str(c1) + " count2:" + str(c2))
	
	rec0 = db2.read(0)
	rec1 = db2.read(1)
	print("db2.rec0:" + str(rec0))
	print("db2.rec1:" + str(rec1))
	
	db1.close()
	db2.close()

	#records():

	#TODO, reads and writes without closing each time must work
	## they don't a the moment?
	
	
if __name__ == "__main__":
	#delete test.txt
	testLock()
	#testWriter()
	#testReader()  
	#testIndex()
	#testDatabase2()

#END
