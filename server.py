import cv2
import numpy
import json
import os
import collections
import operator
import glob
import sys
from flask import Flask,render_template
from PIL import Image
from speech import respond
import socket
import base64
lb=100
last=""
cascadePath="haarcascade_frontalface_default.xml"
faceCascade=cv2.CascadeClassifier(cascadePath)
recognizer=cv2.createLBPHFaceRecognizer()
recognizer.load("rec.xml")
label={1:"Rishu",2:"Bholu",3:"Mom",100:"None"}
# Used for timing
FLANN_INDEX_KDTREE=1
files = []
stack=[]
matcher = None
di={1:"Bed Room",2:"Common Space",3:"Couch",4:"Kitchen",5:"Entrance",7:"Dining Table",8:"temple"}
def get_image(image_path):
	print image_path
	return cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
def recvall(sock, count):
    buf = b''

    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    #print buf
    return buf

def get_image_features(image):
	# Workadound for missing interfaces
	sift = cv2.SIFT()
	surf = cv2.FeatureDetector_create("SURF")
	surf.setInt("hessianThreshold", 60)
	surf_extractor = cv2.DescriptorExtractor_create("SURF")
	#kp1, des1 = sift.detectAndCompute(img1,None)
	# Get keypoints from image
	keypoints = surf.detect(image, None)
	# Get keypoint descriptors for found keypoints
	keypoints, descriptors = surf_extractor.compute(image, keypoints)
	#keypoints,descriptors=sift.detectAndCompute(image,None)
	return keypoints, numpy.array(descriptors)
	#return keypoints,descriptors
def trained_index():
	flann_params = dict(algorithm = 1, trees = 4)
	matcher = cv2.FlannBasedMatcher(flann_params, {})
	l=glob.glob("*.npy")
	for i in l:
		f=i.split(".jpg")[0]
		files.append(f)
		descriptors=numpy.load(i)
		matcher.add([descriptors])
	matcher.train()
	return matcher
def train_index():
	# Prepare FLANN matcher
	flann_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 3)
	matcher = cv2.FlannBasedMatcher(flann_params, dict(checks=50))
	#fp=open("abc.xml","wb")
	# Train FLANN matcher with descriptors of all images
	co=0
	for f in os.listdir("img/"):
		co+=1
		print "Processing " + f
		image = get_image("./img/%s" % (f,))
		keypoints, descriptors = get_image_features(image)
		#print descriptors
		numpy.save(f+".npy",descriptors)
		matcher.add([descriptors])
		files.append(f)

	print "Training FLANN."
	matcher.train()
	#matcher.save_index("record.xml")
	#matcher.save("record.xml")
	#fp.write(matcher)
	print "Done."
	return matcher

def match_image(index, image,lb):
	lb1=lb
	# Get image descriptors
	image = get_image(image)
	keypoints, descriptors = get_image_features(image)
	# Find 2 closest matches for each descriptor in image
	matches = index.knnMatch(descriptors, k=2)
	
	# Cound matcher for each image in training set
	print "Counting matches..."
	count_dict = collections.defaultdict(int)
	for match in matches:
		# Only count as "match" if the two closest matches have big enough distance
		if match[0].distance < 0.7 * match[1].distance:
			image_idx = match[0].imgIdx
			count_dict[files[image_idx]] += 1
		
	#message="espeak 'hi "+label[lb]+"'"
	#os.system(message)
	# Get image with largest count
	matched_image = max(count_dict.iteritems(), key=operator.itemgetter(1))[0]

	# Show results
	print "Images", files
	print "Counts: ", count_dict
	print "==========="
	print "Hit: ", matched_image,count_dict[matched_image]
	print "==========="
	count=count_dict[matched_image]
	env={}
	mapping=int(matched_image.split(".")[0].replace("scene",""))
	print lb,mapping,count
	if lb==100:
		env["person"]="unknown"
		message="espeak -s 155 'There is no person known here..'"
		#os.system(message)
		if count>=30:
			message="espeak -s 155  'The location is"+di[mapping]+"'"
			#os.system(message)
			env["message"]=message

		elif count>=20 and count<30:
			message="espeak -s 155 'The location probably is"+di[mapping]+"'"
			env["message"]=message
			#os.system(message)
		else:
			message="espeak -s 155 'Feebly I can say that it is "+di[mapping]+"'"
			env["message"]=message
			#os.system(message)
	else:
		welcome="espeak -g 13 -s 155 'Hi "+label[lb]+" What would you like to know about me?"+"'"
		env["person"]=label[lb]
		#os.system(welcome)
		#print "Hello"
		if count>=30:
			message="espeak -s 155 'I am also able to locate you. You are at "+di[mapping]+"'"
			print message
			#os.system(message)
			env["message"]=message
		elif count>=20 and count<30:
			message="espeak  -g 13  -s 155 'I am a bit certain you are at "+di[mapping]+"'"
			#os.system(message)
			env["message"]=message
		else:
			print mapping
			message="espeak -s 155 'Feeble intuitions tell me you are at "+di[mapping]+"'" 
			#os.system(message)
			env["message"]=message
	lb=100
	stack.append(env)
	return matched_image,count
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind(("192.168.0.3",5001))
s.listen(True)
flann_matcher = trained_index()
while True:
	conn, addr = s.accept()
	print addr
	#length=conn.recv(16)
	#print length
	length = recvall(conn,16)
	#if length==None:
	#	continue

	data = recvall(conn, int(length))
	data=json.loads(data)
	print data["type"]
	if data["type"]=="speech":

		info=data["data"]
		if len(stack)==0:
			di={"metadata":last,"instruction":info}
			respond(di)
		else:
			last=stack.pop()

			di={"metadata":last,"instruction":info}
			respond(di)
	else:
		stringData=data["data"]
		data=base64.decodestring(stringData)
		#print stringData,length
		with open("img.jpg","wb") as f:
			f.write(data)
		predict_image_pil=Image.open("img.jpg").convert('L')
		predict_image=numpy.array(predict_image_pil)
		faces = faceCascade.detectMultiScale(
					predict_image,
	                scaleFactor=1.2,
	                minNeighbors=5,
	                minSize=(30, 30),
	                flags = cv2.cv.CV_HAAR_SCALE_IMAGE
	            )
		for (x,y,w,h) in faces:
			nbr_predicted,conf=recognizer.predict(cv2.resize(predict_image[y:y+h,x:x+w],(40,40),interpolation=cv2.INTER_CUBIC))
			print nbr_predicted,conf
			if conf<50:
				lb=nbr_predicted
	    	cv2.rectangle(predict_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
	    	cv2.imshow("facefound",predict_image[y:y+h,x:x+w])
	    	cv2.waitKey(1000)
		count=match_image(flann_matcher,"img.jpg",lb)
		lb=100
		cv2.imshow("display",cv2.resize(predict_image,(600,600),interpolation=cv2.INTER_CUBIC))
		cv2.waitKey(2000)
		cv2.destroyAllWindows() 