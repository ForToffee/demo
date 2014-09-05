# Wait.py  06/08/2014  D.J.Whale

try:
  import thread # python2
except ImportError:
  import _thread as thread # python3
  
def trace(msg):
  pass#print(str(msg))
  
# Wait for a completion of an asynchronous call.
# A call is started off, and this is passed as the completion handler.
# On construction, a timer is started. Either the timer times out,
# or the completion handler is called.
# If a timeout occurs, an error is returned. If the completion handler
# is called, it can choose to parse the incoming response
# and turn that into a completion result, but the default action is
# to assume that if a message comes back, it has completed.
# you can override that behaviour.

# TODO add timeout behaviour too, so that the lock is released
# when the timer times out

class WaitComplete():
  OK     = 0
  FAILED = 1
  
  def __init__(self, timeout=None):
    self.timeout = timeout
    self.lock = thread.allocate_lock()
    
  def start(self, timeout=None):
    """Start the completion monitor"""
    trace("start")
    if timeout != None:
      self.timeout = timeout
    self.waiting = True
    self.lock.acquire()
    #trace("start:locked")    
    # python uses bound-methods, which is a closure of the
    # object instance and the method reference. Calling a bound-method
    # calls the function with the correct object instance.
    return self.completed
    
  def completed(self, *args):
    """Call this when completed"""
    trace("completed")
    #TODO:stop the timeout, if it is running
    self.result  = self.OK # default is to assume it's ok
    self.waiting = False #TODO release a lock
    # we need to be resilient to spurious callbacks
    if self.lock.locked():
      self.lock.release()
    #trace("completed:unlocked")
    
    # can override this to provide *args parsing, to work out
    # if it was an OK or FAILED completion
    
  def wait(self):
    """Blocking wait for completion"""
    trace("wait")
    #trace("wait:blocking")
    self.lock.acquire()
    #will block here until the lock is released on completion
    #trace("wait:unblocked:" + str(self.result))
    return (self.result == self.OK) 
    
  def check(self):
    """Poll to see if it has completed"""
    return self.lock.locked()
    
        
# END
