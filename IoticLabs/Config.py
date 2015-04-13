# Config.py  27/03/2015  D.J.Whale
#
# Simple configuration settings access.
# Provides facilities for accessing a .cfg file tied to a script,
# command line arguments, or defaults, with priorities between each.

def trace(msg):
    print(str(msg))


def cast(data, toType=None):
    if toType == None:
        return data # Don't even try to cast it, leave it unchanged

    if data == None:
        return data

    if type(toType) == str:
        return str(data)
    if type(toType) == int:
        return int(data)
    if type(toType) == float:
        return float(data)
    if type(toType) == bool:
        return bool(data)

    raise RuntimeError("Cannot cast, unsupported destination type:" + str(type(toType)))


# BASE CLASS ------------------------------------------------------------------
#
# The base class of all Config structures

class Base():
    def __init__(self):
        pass


    def keyExists(self, key):
        try:
            k = self.get(key)
            return True
        except KeyError:
            return False


    def get(self, key):
        # return KeyError, or value
        raise KeyError(key)


    def put(self, key, value):
        # not all configs are writeable, read only by default
        raise RuntimeError("read only")


    def getKeys(self, prefix=None):
        # return list view of all keys matching prefix
        return []


    def dump(self):
        # Dump config on stdout, for diagnostics
        keys = self.getKeys()
        for k in keys:
            print(str(k) + ":" + str(self.get(k)))


    def __repr__(self):
        result = ""
        keys = self.getKeys()
        first = True
        for k in keys:
            if not first:
                result += '\n'
            result += str(k) + ":" + str(self.get(k))
            first = False
        return result


# MEMORY CLASS ----------------------------------------------------------------
#
# A config class that just lives in memory, with no persistent version.

class Memory(Base):
    def __init__(self):
        Base.__init__(self)
        self.cache = {}


    def put(self, key, value):
        self.cache[key] = value


    def get(self, key):
        return self.cache[key]


    def getKeys(self, prefix=None):
        if prefix == None:
            return self.cache.keys()
        else:
            keys = []
            for k in self.cache:
                if k.startswith(prefix):
                    keys.append(k)
            return keys


# ARGS CLASS ------------------------------------------------------------------
#
# sys.argv is a list numbered from 0, with each argument. Element 0 is
# the filename (mac) or full path(windows) of the script name.
#
# We assume args encoding of key=value in each entry. A key only will
# be represented as a key with value None.

#TODO: Add parser for key=value
#TODO might add parser for - and -- prefixes also, later?
#TODO might add parser for lists of values later (e.g. lists of globbed filenames)

class Args(Base):
    def __init__(self, args):
        Base.__init__(self)
        self.args   = args #keep a copy just in case
        self.config = self.buildMapFromList(args, start=1)


    @staticmethod
    def buildMapFromList(items, start=0):
        # Build a map from a list of items
        theMap = {}
        for i in range(start, len(items)):
            item = items[i]
            k,v = Args.splitKeyValue(item)
            theMap[k] = v
        return theMap


    @staticmethod
    def splitKeyValue(line):
        # Split key=value
        if line == None or len(line) == 0:
            return None, None

        try:
            equalsPos = line.index('=')
        except ValueError:
            return line, None # Just the key
        key = line[:equalsPos]
        value = line[equalsPos+1:]
        return key,value


    def get(self, key):
        # Get the value for this key
        # return KeyError if not found
        return self.config[key]


    def getKeys(self, prefix=None):
        # Get a list of all keys in self.args that match prefix, or all of them
        if prefix == None:
            return self.config.keys()
        else:
            keys = []
            for k in self.config.keys():
                if k.startswith(prefix):
                    keys.append(k)
            return keys


# FILE CLASS ------------------------------------------------------------------
#
# A config that is loaded from a persistent version on disk.
# If the version on disk changes, this sees the changes immediately.
#TODO: Might make auto refresh semantics optional?

class File(Base):
    def __init__(self, filename=None):
        Base.__init__(self)
        if filename == None:
            filename = self.guessFilename()
        self.filename  = filename
        self.lastwrite = None
        self.keycache  = None


    def get(self, key):
        self.updateKeyCache()
        try:
            index = self.keycache.index(key)
        except ValueError:
            raise KeyError(key)
        value = self.readValueFor(key)
        return value


    def updateKeyCache(self):
        # Check the key cache, and update it if the file has changed
        refresh = False
        if self.keycache == None:
            refresh = True
        else:
            # get timestamp of last write
            lastwrite = self.getLastWriteTimestamp()
            if lastwrite > self.lastwrite:
                refresh = True
                self.lastwrite = lastwrite

        if refresh:
            self.keycache = self.readKeys()


    @staticmethod
    def splitKeyValue(line):
        # Split a line into a key and a value
        line = line.strip()
        if line == None or len(line) == 0:
            return None, None

        try:
            colonpos = line.index(':')
            key = line[:colonpos]
            value = line[colonpos+1:]
        except ValueError:
            key  = line
            value = None
        return key, value


    def readKeys(self):
        # Read all keys into a memory list
        #trace("trying to open file:" + str(self.filename))
        f = open(self.filename, "rt")
        keys = []
        for line in f.readlines():
            k, v = self.splitKeyValue(line)
            if k != None:
                keys.append(k)
        f.close()
        return keys


    def readValueFor(self, key):
        # Read the value associated with this key.
        # KeyError if key not found.
        f = open(self.filename, "rt")
        for line in f.readlines():
            k, v = self.splitKeyValue(line)
            if k != None and k == key:
                f.close()
                return v
        f.close()
        return KeyError(key)


    def getLastWriteTimestamp(self):
        # Get the timestamp of the last time this file was written
        import time
        return time.time() # TODO not yet written


    def getKeys(self, prefix=None):
        # get all keys, or those matching a prefix
        self.updateKeyCache()
        if prefix == None:
            return self.keycache
        else:
            keys = []
            for k in self.keycache:
                if k.startswith(prefix):
                    keys.append(k)
            return keys


# ARGSFILE --------------------------------------------------------------------
#
# Combination of sys.argv parser, and a file parser.
# Note that the filename can be provided, but can also be overriden
# with sys.argv 'config' parameter.


class ArgsFile(Base):
    # A config that has a file, but overrides allowed by args
    def __init__(self, args, filename):
        Base.__init__(self)
        self.argsconfig = Args(args)

        # See if args provides a config filename
        if self.argsconfig.keyExists("config"):
            filename = self.argsconfig.get("config")

        # Open config parameter name, or name provided by caller, if none.
        # If filename is 'None", don't try to open it.
        if filename == None:
            self.fileconfig = None
        else:
            if not os.path.isfile(filename):
                self.fileconfig = None
            else:
                self.fileconfig = File(filename)


    def getArgs(self):
        """Get an Args() view of the command line arguments"""
        return self.argsconfig


    def getFile(self):
        """Get a File() view of the file persistent settings"""
        return self.fileconfig


    def get(self, key):
        """Get from args, or file. KeyError if nothing found in either"""
        # Note will always return a string, as that is what is read.

        # args item overrides item in file
        try:
            # Does args hold a value for this key?
            value = self.argsconfig.get(key)
            return value

        except KeyError as e:
            # Is the associated .cfg file missing?
            if self.fileconfig == None:
                raise KeyError("no config file, can't find:" + str(key))

            # Does the .cfg file hold a value for this key?
            value = self.fileconfig.get(key)
            return value


    def getKeys(self, prefix=None):
        # Get list of merged keys from both args and file
        keys1 = self.argsconfig.getKeys()

        if self.fileconfig == None:
            #trace(" no file, returning keys1:" + str(keys1))
            return keys1

        keys2 = self.fileconfig.getKeys()
        #trace(" keys1:" + str(keys1))
        #trace(" keys2:" + str(keys2))
        for idx in range(0, len(keys1)):
            k = keys1[idx]
            try:
                i = keys2.index(k)
                #trace(" keys2 already has:" + str(k))
            except ValueError:
                #trace(" keys2 does not have:" + str(k))
                keys2.append(k)

        #trace(" final keys merged:" + str(keys2))
        return keys2



# DEFAULT INSTANCES -------------------------------------------------------

import sys
import os
fullPath    = os.path.abspath(sys.argv[0])
pathAndName = os.path.splitext(fullPath)[0]
cfgName     = pathAndName + ".cfg"

values = ArgsFile(sys.argv, cfgName)


# MODULE WRAPPER --------------------------------------------------------------
#
# Make this Config.py module masquerade as a class, so we can have some
# nice semantics in the user code, such as:
#   import Config as cfg
#   print(cfg)
#   a = cfg("name")
#   a = cfg.get("name")
#   a = cfg.getKeys()
#
# It also hides all the other inner stuff from this module, thus making it
# private. The Wrapper() ends up being a firewall that protects the innards
# of this module from unapproved reflection.
#
# The semantics of defaults with get() and __call__ are added to make this
# really useful:
# import Config as cfg
# a = cfg("fred") # KeyError if not found
# a = cfg("fred", None) # return None if not found
# a = cfg("fred", "n") # return str(n) if not found
# a = cfg("fred", 33) # return int(33) if not found, int(value) if found
# i.e note the cast that is added if a default is provided, so that
# the type comes back in a form you want. Only base types such as int,str,bool,float.

class Wrapper():
    def __init__(self, inner):
        self.inner = inner


    def __repr__(self):
        return str(self.inner)


    def __call__(self, key, **kwargs):
        """Alias for get()"""
        return self.get(key, **kwargs)


    def get(self, key, **kwargs):
        """Get value, cast to type of default if provided, default if no value"""
        # Throws KeyError if cannot find key and no default provided.
        has_default = kwargs.has_key("default")
        if has_default:
            default = kwargs["default"]

        try:
            value = self.inner.get(key)
            if has_default:
                return me.cast(value, default)
            else:
                return value

        except KeyError as e:
            if not has_default:
                raise e
            return default


    def getKeys(self, prefix=None):
        """Get a list of supported keys (that match optional prefix)"""
        return self.inner.getKeys(prefix)



# Replace the meta-model for this module with a protective class wrapper

import sys
me = sys.modules[__name__]
sys.modules[__name__] = Wrapper(values)


# END



