#!/usr/bin/python

# Simple pic/mov renamer script.
# by Albert Zeyer
# code under zlib

# Adds a date (eg. "2011_01_22__") as a prefix to each file.
# Asks for confirmation, so it is safe to just try out and see what it would do.


from glob import *
from recglob import *
from cleanupstr import *
import sys, os
import better_exchook
better_exchook.install()

def usage():
	print "usage:", sys.argv[0], "<dir>"
	print "Asks for confirmation before it does any action."
	
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

def file_time_creation(f):
	import os, time
	stats = os.stat(f)
	try:
		t = stats.st_birthtime
	except Exception:
		t = stats.st_ctime
	return time.strftime("%Y:%m:%d %H:%M:%S",time.localtime(t))
	
def iminfo(f):
	try:
		info = cleanup_exif_tags(exif.getexif(f))
	except Exception:
		info = {}
	if not "DateTime" in info:
		info["DateTime"] = file_time_creation(f)
	return info

def user_input(text, convfunc):
	while True:
		try:
			s = raw_input(text)
			return convfunc(s)
		except Exception, e:
			print "Error:", e

def str_to_bool(s):
	if s.lower() in ["y", "yes", "ja", "j", "1"]: return True
	if s.lower() in ["n", "no", "nein", "0"]: return False
	raise Exception, "I don't understand '" + s + "'; please give me an Y or N"
	
files = {}
errors = {}

for f in recglob(dir + "/*.{jpeg,jpg,JPG,mov,MOV,png,PNG}"):
	try:
		info = iminfo(f)
		prefix = info["DateTime"].replace(":", "_")[0:10] # get eg. "2011_01_22"
		prefix += "__"
		newfn = os.path.dirname(f) + "/" + prefix + os.path.basename(f)
		if os.path.exists(newfn):
			errors[f] = os.path.basename(newfn) + " already exists"
		elif os.path.basename(f)[0:len(prefix)] == prefix:
			errors[f] = os.path.basename(f) + " already has the prefix '" + prefix + "'"			
		else:
			files[f] = newfn
	except Exception, e:
		errors[f] = str(e)

while True:
	if len(files) > 0:
		print "Renames:"
		for old, new in sorted(files.items()):
			print "", old, "->", os.path.basename(new)
		print ""
	
	if len(errors) > 0:
		print "Errors (i.e. excluded files):"
		for f, err in errors.iteritems():
			print "", f, ":", err
		print ""
	
	if len(files) == 0:
		print "No files to rename. Quitting."
		quit()
	
	ok = user_input("Confirm? (Y/N) ", str_to_bool)
	if ok:
		for old, new in sorted(files.items()):
			os.rename(old, new)
		print "All renames successfull."
		quit()
	else:
		print "Abborting."
		quit()
