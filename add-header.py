#!/usr/bin/python
# Adds header on all source code files in a project.

import sys, os
from recglob import recglob
from pprint import pprint

path = sys.argv[1]
assert os.path.isdir(path)

comment = "\n".join(sys.argv[2:])

print "Adding this comment:"
print "\n".join(["  " + s for s in comment.splitlines()])

filetypes = {
	"py": "#",
	"c": "//",
	"cpp": "//",
}

filelist = []
for t in filetypes.keys():
	filelist += list(recglob(path + "/*." + t))

def hasNoCopyrightHeader(fn):
	f = open(fn)
	lines = "".join([f.readline() for i in range(10)])
	if "GNU" in lines: return False
	if "license" in lines: return False
	if "copyright" in lines.lower(): return False
	if "public domain" in lines.lower(): return False
	if "zlib" in lines.lower(): return False
	return True

filelist = filter(hasNoCopyrightHeader, filelist)

def patch(lines, prefix):
	lines = list(lines)
	startIndex = 0
	if len(lines) > startIndex and lines[startIndex].startswith("#!"): startIndex += 1
	if len(lines) > startIndex and lines[startIndex].startswith("# -*- coding"): startIndex += 1
	lines[startIndex:startIndex] = [
		prefix + s + "\n" for s in comment.splitlines()
	]
	return lines

for fn in filelist:
	print fn
	lines = open(fn).readlines()
	ext = os.path.splitext(fn)[1][1:]
	prefix = filetypes[ext] + " "
	lines = patch(lines, prefix)
	open(fn, "w").writelines(lines)
