# config.py

# Put the number of the SD-Card here

MY_NUMBER = None





#---- Don't change anything below this line -----------------------

MY_COMPUTER = "IOT_Pi_" + str(MY_NUMBER)

if MY_NUMBER == None:
  print("")
  print("*" * 79)
  print("**** You must set your computer number in config.py ****")
  print("*" * 79)
  print("")

  import sys
  sys.exit(1)

# END

