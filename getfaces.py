import face_recognition
import numpy as np
import cv2
import random
import string
import os
import math
import argparse


os.system('cls' if os.name=='nt' else 'clear')

parser = argparse.ArgumentParser();
parser.add_argument('-i', type=str, help='Image of target face to scan for.', required=True)
parser.add_argument('-v', type=str, help='Video to process', required=True)
parser.add_argument('-t', type=float, help='Tolerance of face detection, lower is stricter. (0.1-1.0)', default=0.6)
parser.add_argument('-f', type=int, help='Amount of frames per second to extract.', default=1)
parser.add_argument('-c', type=str, help='Whether to crop the frame or not (true/false), default true', default="true")
args = vars(parser.parse_args())

if args['t'] > 1.0:
	args['t'] = 1.0
elif args['t'] < 0.1:
	args['t'] = 0.1

tol = args['t']
xfps = args['f']
targfname = args['i']
vidfname = args['v']

if xfps < 1:
	xfps = 1

print("Target filename: " + targfname + ".")
print("Video filename: " + vidfname + ".")
print("Tolerance: " + str(tol) + ".")

if(cv2.ocl.haveOpenCL()):
	cv2.ocl.setUseOpenCL(True)
	print("Using OpenCL: " + str(cv2.ocl.useOpenCL()) + ".")

target_image = face_recognition.load_image_file(targfname)
outdir = str(str(os.path.splitext(targfname)[0]) + "_output");

#check if output directory already exists, and if not, create it
os.makedirs(outdir, exist_ok=True)

print("Output directory: " + outdir + ".")

try:
	target_encoding = face_recognition.face_encodings(target_image)[0]
except IndexError:
	print("No face found in target image.")
	raise SystemExit(0)

input_video = cv2.VideoCapture(vidfname)

framenum = 0
vidheight = input_video.get(4)
vidwidth = input_video.get(3)
vidfps = input_video.get(cv2.CAP_PROP_FPS)
totalframes = input_video.get(cv2.CAP_PROP_FRAME_COUNT)
outputsize = 256, 256

if xfps > vidfps:
	xfps = vidfps

print("Frame Width: " + str(vidwidth) + ", Height: " + str(vidheight) + ".")

known_faces = [
	target_encoding
]

def random_string(length):
	return ''.join(random.choice(string.ascii_letters) for m in range(length))

def get_encodings(directory):
	for file in os.listdir("./" + directory + "/"):
		imgl = face_recognition.load_image_file("./" + directory + "/" + file)
		enc = face_recognition.face_encodings(enc)[0]
		known_faces.append(enc)

#switch to output directory
os.chdir(str(os.path.splitext(targfname)[0]) + "_output")

#spacer
print(" ")

while(input_video.isOpened()):
	input_video.set(1, (framenum + (vidfps/xfps)))
	framenum += vidfps/xfps
	ret, frame = input_video.read()

	if not ret:
		break

	percentage = (framenum/totalframes)*100
	print("Processing frame " + str(int(framenum)) + "/" + str(int(totalframes)) + str(" (%.2f%%)" % percentage), end='\r')
	
	rgb_frame = frame[:, :, ::-1]
	
	face_locations = face_recognition.face_locations(rgb_frame)
	face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
	
	for fenc, floc in zip(face_encodings, face_locations):
		istarget = face_recognition.compare_faces(known_faces, fenc, tolerance=float(tol))

		if istarget[0] and not (args['c'].lower() == 'true'):
			cv2.imwrite(("0" + random_string(15) + ".jpg"), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 98])
			continue
	
    	#if the face found matches the target
		elif istarget[0] and (args['c'].lower() == 'true'):
			top, right, bottom, left = floc
			facefound = True

			#squaring it up
			if (bottom - top) > (right - left):
				right = left + (bottom - top)
			elif (right - left) > (bottom - top):
				bottom = top + (right - left)

			padding = (bottom - top)/2
			
			if((top - padding >= 0) and (bottom + padding <= vidheight) and (left - padding >= 0) and (right + padding <= vidwidth)):
				croppedframe = frame[int(top - padding):int(bottom + padding), int(left - padding):int(right + padding)]
				
				#if the image is too small, resize it to outputsize
				cheight, cwidth, cchannels = croppedframe.shape
				if (cheight < 256) or (cwidth < 256):
					croppedframe = cv2.resize(croppedframe, outputsize, interpolation=cv2.INTER_CUBIC)

				#print("Writing image.                                   ", end='\r')
				cv2.imwrite(("0" + random_string(15) + ".jpg"), croppedframe, [int(cv2.IMWRITE_JPEG_QUALITY), 98])
input_video.release()
