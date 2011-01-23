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

from PIL import Image
from PIL.ExifTags import TAGS

def get_exif(fn):
    ret = {}
    i = Image.open(fn)
    info = i._getexif()
    for tag, value in info.iteritems():
		try:
			decoded = TAGS.get(tag, tag)
			ret[decoded] = value
		except:
			pass
    return ret

def cleanup_exif_tags(exif):
	ret = {}
	for tag, value in exif.iteritems():
		if type(tag) is int: continue
		if tag == "MakerNote": continue
		if type(value) is str:
			value = cleanupstr(value).strip()
		ret[tag] = value
	return ret
	
allexif = {}
for f in recglob(dir + "/*.{jpeg,jpg,JPG}"): #recglob(dir + "/*.{jpg,jpeg}"):
	print f, ":",
	try:
		exif = cleanup_exif_tags(get_exif(f))
		print exif["DateTime"]
		allexif.update(exif)
	except Exception, e:
		print e

for tag, value in allexif.iteritems():
	print tag, ":", value
	