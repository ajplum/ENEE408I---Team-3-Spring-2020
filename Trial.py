from queue import Queue
import subprocess
from imutils.video import WebcamVideoStream
from imutils.video import VideoStream
import cv2
import imutils
import serial
import serial.tools.list_ports  # for listing serial ports
import time
import os
from enum import Enum
# os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import sys  # command line lib
import glob
import math
import smtplib
import os
import urllib.request
import smtplib
from os.path import basename
from urllib.request import urlopen
import argparse
from collections import deque




# Class/Enums to keep track of some of our last directions sent and to
# send down commands to Arduino via Serial communication
class Direction(Enum):
    FORWARD = 1
    BACKWARD = 2
    LEFT = 3
    RIGHT = 4
    STOP = 5



# Start the webcam streaming operation and set the object attribute to use...
vs = VideoStream(src=1).start()
# Allow camera to warm up...
time.sleep(2.0)


def com_connect():

	ser = serial.Serial('/dev/ttyACM0')  # open serial port
	connection_made = True
	print(ser.name)         # check which port was really used

	return ser


# Send serial command to Arduino. If the last command that we've sent is the same as the one we're trying to send
# now, then ignore it since the Arduino already has the up-to-date command. Note that there's a commented out
# section of this code that made it so that even if the command was a duplicate of the last send one,
# it would still send the command as long as a certain time period had passed. Depending on how the Arduino code
# worked this may have been necessary, but we did not need it.

def send_serial_command(Port,direction_enum, dataToSend):

	# Variables to hold last command sent to Arduino and when it was sent (epoch seconds). Note:
	# lastCommandSentViaSerialTime ended up not being utilized - but its purpose was to send duplicate commands
	# after some certain amount of time in case the Arduino needed it for some reason (it did not with our
	# current design)
	lastCommandSentViaSerial = None
	lastCommandSentViaSerialTime = None


	# If this command is different than the last command sent, then we should sent it
	# Or if it's the same command but it's been 1 second since we last sent a command, then we should send it
	if Port is not None:
		if lastCommandSentViaSerial != direction_enum:  # I think I want to use something different
			Port.write(dataToSend)
			lastCommandSentViaSerial = direction_enum
			lastCommandSentViaSerialTime = time.time()
		else:
			pass  # Do nothing - same command sent recently

	# Call this when closing this openCV process. It will stop the WebcamVideoStream thread, close all openCV
	# windows, and close the SerialPort as long as it exists (if we're connected to an Arduino).



# Follow a person (represented by a green folder). If the second argument (run_py_eyes) is set to True then we'll
def person_following(): # no pygame

	# construct the argument parse and parse the arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-v", "--video",
	help="path to the (optional) video file")
	ap.add_argument("-b", "--buffer", type=int, default=64,
	help="max buffer size")
	args = vars(ap.parse_args())

	# define the lower and upper boundaries of the "green"
	# ball in the HSV color space, then initialize the
	# list of tracked points
	greenLower = (25, 75, 85)
	greenUpper = (50, 220, 255)
	pts = deque(maxlen=args["buffer"])


	# Frame is considered to be 600x600 (after resize)
	# Below are variables to set what we consider center and in-range
	radiusInRangeLowerBound, radiusInRangeUpperBound = 80, 120
	centerRightBound, centerLeftBound = 400, 200
	radiusTooCloseLowerLimit = 250

	# Creating a window for later use
	cv2.namedWindow('result')
	cv2.resizeWindow('result', 600, 600)

	# Variables to 'smarten' the following procedure (see usage below)
	objectSeenOnce = False  # Object has never been seen before
	leftOrRightLastSent = None  # Keep track of whether we sent left or right last

	# TODO delete this block when done
	start = time.time()
	num_frames = 0

	while True:

	    # Grab frame - break if we don't get it (some unknown error occurred)
		frame = vs.read()
		if frame is None:
			print("ERROR - frame read a NONE")
			break

		# handle the frame from VideoCapture or VideoStream
		frame = frame[1] if args.get("video", False) else frame

		# if we are viewing a video and we did not grab a frame,
		# then we have reached the end of the video
		if frame is None:
			break


		# downsize frame to process faster
		frame = imutils.resize(frame, width=600)

		# blur frame to reduce high frequency noise
		blurred = cv2.GaussianBlur(frame, (11, 11), 0)

		# convert frame to hsv color space
		hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)


		# construct a mask for the color "green", then perform
		# a series of dilations and erosions to remove any small
		# blobs left in the mask
		mask = cv2.inRange(hsv, greenLower, greenUpper)
		mask = cv2.erode(mask, None, iterations=2) # TODO: these were 3 or 5 before (more small blob removal)
		mask = cv2.dilate(mask, None, iterations=2)

		# find contours in the mask and initialize the current
		# (x, y) center of the ball
		cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
			cv2.CHAIN_APPROX_SIMPLE)
		cnts = imutils.grab_contours(cnts)
		center = None
		commandString = None


		    # Only proceed if at least one contour was found
		    # If nothing is found, then look around OR send the STOP command to halt movement (depends on situation)
		if len(cnts) == 0:
		# If we haven't seen the object before, then we'll stay halted until we see one. If we HAVE seen the
		# object before, then we'll move in the direction (left or right) that we did most recently
			if not objectSeenOnce:
				send_serial_command(serialPort,Direction.STOP, b'h')
				commandString = "STOP"
			else:  # Object has been seen before
				if leftOrRightLastSent is not None:
					if leftOrRightLastSent == Direction.RIGHT:
						send_serial_command(serialPort,Direction.RIGHT, b'r')
						commandString = "SEARCHING: GO RIGHT"
						send_serial_command(serialPort,Direction.FORWARD, b'f')
						commandString = "MOVE FORWARD"
					elif leftOrRightLastSent == Direction.LEFT:
						send_serial_command(serialPort,Direction.LEFT, b'l')
						commandString = "SEARCHING: GO LEFT"
						send_serial_command(serialPort,Direction.FORWARD, b'f')
						commandString = "MOVE FORWARD"
					else:  # variable hasn't been set yet (seems unlikely), but default to left
						send_serial_command(serialPort,Direction.LEFT, b'l')
						commandString = "DEFAULT SEARCHING: GO LEFT"
						send_serial_command(serialPort,Direction.FORWARD, b'f')
						commandString = "MOVE FORWARD"

		elif len(cnts) > 0:  # Else if we are seeing some object...

		# Find the largest contour in the mask and use it to compute the minimum enclosing circle and centroid
			c = max(cnts, key=cv2.contourArea)
			((x, y), radius) = cv2.minEnclosingCircle(c)
			M = cv2.moments(c)
			center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
			filteredPtsRadius = [radius]

			# Only consider it to a valid object if it's big enough - else it could be some other random thing
			if filteredPtsRadius[0] <= 25:
			    # TODO this is the same code as the block above - I should extract these out to a function
			    # If we haven't seen the object before, then we'll stay halted until we see one
			    # If we HAVE seen the object before, then we'll move in the direction (left or right) that we did
			    # most recently
				if not objectSeenOnce:
					send_serial_command(serialPort,Direction.STOP, b'h');
					commandString = "STOP";
				else:  # Object has been seen before
					if leftOrRightLastSent is not None:
						if leftOrRightLastSent == Direction.RIGHT:
							send_serial_command(serialPort,Direction.RIGHT, b'r');
							commandString = "SEARCHING: GO RIGHT"
							send_serial_command(serialPort,Direction.FORWARD, b'f')
							commandString = "MOVE FORWARD"
						elif leftOrRightLastSent == Direction.LEFT:
							send_serial_command(serialPort,Direction.LEFT, b'l');
							commandString = "SEARCHING: GO LEFT"
							send_serial_command(serialPort,Direction.FORWARD, b'f')
							commandString = "MOVE FORWARD"
					else:  # variable hasn't been set yet (seems unlikely), but default to left
						send_serial_command(serialPort,Direction.LEFT, b'l');
						commandString = "DEFAULT SEARCHING: GO LEFT"
						send_serial_command(serialPort,Direction.FORWARD, b'f')
						commandString = "MOVE FORWARD"

			else:  # This object isn't super small ... we should proceed with the tracking

			    # Set objectSeenOnce to True if isn't already
				if not objectSeenOnce:
					objectSeenOnce = True
	
			# only proceed if the radius meets a minimum size
				if filteredPtsRadius[0] > 10:
			    #  draw the circle on the frame TODO consider removing this eventually - could speed things up (barely)
					cv2.circle(frame, (int(x), int(y)), int(filteredPtsRadius[0]), (0, 255, 255), 2)
					cv2.circle(frame, center, 5, (0, 0, 255), -1)
					print(filteredPtsRadius[0])
					filteredPtsX = [center[0]]
					filteredPtsY = [center[1]]

			    # Check radius and center of the blob to determine robot action
			    # What actions should take priority?
			    # 1. Moving Backward (only if it's super close)
			    # 2. Moving Left/Right
			    # 3. Moving Forward/Backward
			    # Why? Because if we're too close any turn would be too extreme. We need to take care of that first

					if filteredPtsRadius[0] > radiusTooCloseLowerLimit:
						commandString = "MOVE BACKWARD - TOO CLOSE TO TURN"
						send_serial_command(serialPort,Direction.BACKWARD, b'b')
					elif filteredPtsX[0] > centerRightBound:
						commandString = "GO RIGHT"
						send_serial_command(serialPort,Direction.RIGHT, b'r')
					if leftOrRightLastSent != Direction.RIGHT:
						leftOrRightLastSent = Direction.RIGHT
					elif filteredPtsX[0] < centerLeftBound:
						commandString = "GO LEFT"
						send_serial_command(serialPort,Direction.LEFT, b'l')
					if leftOrRightLastSent != Direction.LEFT:
						leftOrRightLastSent = Direction.LEFT
					elif filteredPtsRadius[0] < radiusInRangeLowerBound:
						commandString = "MOVE FORWARD"
						send_serial_command(serialPort,Direction.FORWARD, b'f')
					elif filteredPtsRadius[0] > radiusInRangeUpperBound:
						commandString = "MOVE BACKWARD"
						send_serial_command(serialPort,Direction.BACKWARD, b'b')
					elif radiusInRangeLowerBound < filteredPtsRadius[0] < radiusInRangeUpperBound:
						commandString = "STOP MOVING - IN RANGE"
						send_serial_command(serialPort,Direction.STOP, b'h')


				else:
					print(filteredPtsRadius[0])
		    # The below steps are run regardless of whether we see a valid object or not ...


		# Close application on 'q' key press, or if the queue is not empty (there's some command to respond to).
		# show the frame to our screen
		cv2.imshow("Frame", frame)
		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):
			send_serial_command(serialPort,Direction.STOP, b'h')
			# We've been requested to leave ...
			# Don't destroy everything - just destroy cv2 windows ... webcam still runs
			cv2.destroyAllWindows()
			break





serialPort = com_connect()
person_following()

