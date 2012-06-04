#!/usr/bin/python

# code by Albert Zeyer, 2012-06-04
# code under zlib licence
# more: https://github.com/albertz/helpers

import sys, os
files = sys.argv[1:]
debug = False

if not files:
	print >>sys.stderr, "usage:", sys.argv[0], "<files>"
	sys.exit(1)
	
for f in files:
	if not os.path.exists(f):
		print >>sys.stderr, "file", repr(f), "does not exists"
		sys.exit(1)

# script around FSPathMoveObjectToTrashSync
# https://developer.apple.com/library/mac/#documentation/Carbon/Reference/File_Manager/Reference/reference.html#//apple_ref/c/func/FSPathMoveObjectToTrashSync

import ctypes
CoreServices = ctypes.CDLL("/System/Library/Frameworks/CoreServices.framework/CoreServices")

#OSStatus FSPathMoveObjectToTrashSync (
#   const char *sourcePath,
#   char **targetPath,
#   OptionBits options
#);

OSStatus = ctypes.c_int32 # MacTypes.h
OptionBits = ctypes.c_uint32 # MacTypes.h

rm = CoreServices.FSPathMoveObjectToTrashSync
rm.argtypes = (ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p), OptionBits)
rm.restype = OSStatus

for f in files:
	trashfn = ctypes.c_char_p()
	res = rm(f, ctypes.pointer(trashfn), 0)
	if debug:
		print "rm", repr(f), "->", res, repr(trashfn.value) if trashfn else "NULL"
	if res != 0:
		print "error", res, "on file", repr(f)
		sys.exit(1)
	
