# NameToCoordinates.py  28/08/2014  D.J.Whale
#
# Convert a name string into coordinates on a map
# Useful for creating locations for things that don't have a location.

import random

NAME = "IOTIC LABS"
OFFSET = -(65+9) # I represens zero
MODULO = 16 # base 16 so could encode as hex too


def getNumbers(name, offset, modulo):
  result = [[]]
  i = 0
  
  for ch in name:
    if ch == " ":
      i += 1
      result.append([])
    else:
      n = ord(ch)
      n += offset
      n = n % modulo
      result[i].append(n)
  return result
  
  
def makeCoord(numbers):
  coord = None
  for n in numbers:
    if coord == None:
      coord = str(n) + "."
    else:
      coord += str(n)
  return coord

  
def tidyName(name):
  if name == None:
    return NAME
    
  name = name.strip()
  if len(name) == 0:
    return NAME

  if name.find(" ") == -1: # there are no spaces
    l = len(name)
    if l < 2:
      # double it up
      return name + " " + name
    if l < 8:
      # split in half
      half = l/2
      return name[0:half] + " " + name[half:]
    # just split into two words of 4 chars each
    return name[0:4] + " " + name[4:8]
    
  # Name has one or more spaces, use 4 chars of first two words
  first, second = name.split(" ", 1)
  if len(first) > 4:
    first = first[:4]
  if len(second) > 4:
    second = second[:4]
    
  return first + " " + second


def makeDDD(nums):
  result = str(nums[0]) + "."
  nums = nums[1:]
  if len(nums) == 0:
    result += "0"
  else:
    for n in nums:
      if n > 99:
        n = n % 100
      #if n < 9:
      #  result += "0"
      result += str(n)
  try:
    r = float(result)
    return r
  except:
    return 0.0, 0.0
    
  
def getCoords(name):
  name = tidyName(name)
  c = getNumbers(name, OFFSET, MODULO)
  return makeDDD(c[0]), makeDDD(c[1])
  


def test():
  tests = [
    # None
    None,
    
    # empty string
    "   ",
    
    # single char
    "a",
    
    # two chars
    "ab",
    
    # two chars one space
    "c d",
    
    # one word, shorter than 8
    "fred",
    
    # one word, 8
    "jonathan",
    
    # one word, bigger than 8
    "charlotte",
    
    # two words, both shorter than 4
    "the cat",
    
    # two words, both bigger than 4
    "david whale",
    
    # three words
    "david john whale"
  ]
  
  for t in tests:
    print(t, tidyName(t), getNumbers(tidyName(t), OFFSET, MODULO), getCoords(t)) 
  
  
if __name__ == "__main__":
  test()
  #  c = getNumbers(NAME, OFFSET, MODULO)
  #  print(str(c))
  #  print(makeCoord(c[0]) + "," + makeCoord(c[1]))
  #print(getCoords(NAME))

# END

