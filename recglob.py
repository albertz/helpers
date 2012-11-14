# recursive glob
# by Albert Zeyer
# code under zlib

import os, glob, fnmatchex

# usage: filepattern = dir + "/" + pattern
# filepattern: fnmatchex expr only supported for the basename yet
# this function iterates: dir + "/**/" + pattern
def recglob(filepattern, followlinks=False):
	dir = os.path.dirname(filepattern)
	filepattern = os.path.basename(filepattern)
	
	# use iglob instead of listdir to get a lazy list
	for f in glob.iglob(dir + "/*"):
		if not followlinks and os.path.islink(f) and os.path.isdir(f):
			continue
		if os.path.isdir(f):
			for x in recglob(f + "/" + filepattern, followlinks=followlinks):
				yield x
		else:
			if fnmatchex.fnmatchex(os.path.basename(f), filepattern):
				yield f
