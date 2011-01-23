#!/usr/bin/python

from glob import *
from recglob import *
from cleanupstr import *
import sys, os

def usage(): print "usage:", sys.argv[0], "<dir>"
	
if len(sys.argv) != 2:
	usage()
	quit()

dir = sys.argv[1]
if not os.path.isdir(dir):
	print dir, "is not a directory"
	usage()
	quit()

import exif

def cleanup_exif_tags(exif):
	ret = {}
	for tag, value in exif.iteritems():
		if type(tag) is int: continue
		if tag == "MakerNote": continue
		if type(value) is str:
			value = cleanupstr(value).strip()
		ret[tag] = value
	return ret

def iminfo(f):
	return cleanup_exif_tags(exif.getexif(f))
	
allexif = {}
for f in recglob(dir + "/*.{jpeg,jpg,JPG}"):
	print f, ":",
	try:
		info = iminfo(f)
		if "DateTime" in info:
			print info["DateTime"]
		else:
			print "incomplete EXIF"
		allexif.update(info)
	except Exception, e:
		print e

for tag, value in allexif.iteritems():
	print tag, ":", value
	