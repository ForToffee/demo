# TakePhoto.py  12/08/2014  D.J.Whale
#
# Take a photo with the pi camera and store to a file
# from: http://blog.whaleygeek.co.uk/controlling-the-raspberry-pi-camera-with-python/

import picamera
from time import sleep

WIDTH =  100
HEIGHT = 100
IMAGE_NAME = "image.gif"

# INIT CAMERA
print("initialising camera")
camera = picamera.PiCamera()
camera.vflip = False
camera.hflip = False
camera.brightness = 60

# TAKE A PHOTO TO A FILE
print("taking photo")
camera.start_preview()
sleep(0.5)
camera.capture(IMAGE_NAME, format='gif', resize=(WIDTH,HEIGHT))
camera.stop_preview()

print("look in file:" + IMAGE_NAME)
time.sleep(1)


