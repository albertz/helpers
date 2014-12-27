#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import getopt, sys, io

def usage():
	print("usage: %s -n <spacenum> [-i] [infile]", sys.argv[0])
	exit(1)

try:
	opts, args = getopt.getopt(sys.argv[1:], "in:")
except getopt.GetoptError as e:
	print(e.msg)
	usage()
opts = dict(opts)

if not "-n" in opts: usage()
spacenum = int(opts["-n"])
if spacenum < 1:
	print("spacenum must be >=1")
	usage()
if len(args) > 1: usage()
inplace = "-i" in opts
if inplace and len(args) == 0:
	print("inplace does not make sense for stdin")
	usage()

infile = open(args[0]) if args else sys.stdin
outfile = io.StringIO() if inplace else sys.stdout

while True:
	l = infile.readline()
	if l == "": break	
	
	newl = u''
	curspacenum = 0
	for i in range(0,len(l)):
		c = l[i]
		if c == "\t":
			newl += "\t"
			curspacenum = 0
			continue
		if c == " ":
			curspacenum += 1
			if curspacenum == spacenum:
				newl += "\t"
				curspacenum = 0
			continue
		newl += " " * curspacenum
		newl += l[i:]
		break
		
	outfile.write(newl)

if inplace:
	infile.close()
	infile = open(args[0], "w")
	infile.write(outfile.getvalue())

infile.close()
