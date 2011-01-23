# recursive glob
# by Albert Zeyer
# code under zlib

import os, glob, fnmatchex

def recglob(filepattern, followlinks=False):
	dir = os.path.dirname(filepattern)
	filepattern = os.path.basename(filepattern)
	
	# use iglob instead of listdir to get a lazy list
	for f in glob.iglob(dir + "/*"):
		if not followlinks and os.path.islink(f) and os.path.isdir(f):
			continue
		if os.path.isdir(f):
			for x in recglob(f + "/" + filepattern):
				yield x
		else:
			if fnmatchex.fnmatchex(os.path.basename(f), filepattern):
				yield f
			else:
				print "no match:", f, ",", filepattern
