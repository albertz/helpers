#!/usr/bin/python

import mechanize, sys

import getopt, sys, io

def usage():
        print "usage:", sys.argv[0], "[-d <depth>] <url>"
        exit(1)

try:
        opts, args = getopt.getopt(sys.argv[1:], "d:")
except getopt.GetoptError as e:
        print e.msg
        usage()
opts = dict(opts)

depth = 1
if "-d" in opts: depth = int(opts["-d"])

b = mechanize.Browser()

def filename_for_url(url):
	import urlparse, os
	o = urlparse.urlparse(url)
	return os.path.basename(o.path)

def make_proper_unique_pdffilename(fn):
	import os
	root,ext = os.path.splitext(fn)
	if ext.lower() != ".pdf": ext += ".pdf"
	if os.path.exists(root + ext):
		num = 2
		while os.path.exists(root + "-" + str(num) + ext): num += 1
		root += "-" + str(num)
	return root + ext

def savepdf(h):
	fn = filename_for_url(h.geturl())
	fn = make_proper_unique_pdffilename(fn)
	print fn
	f = open(fn, "wb")
	f.write(h.get_data())
	f.close()

def openurl(h, d):
	if h._headers.type == "text/html":
		if d > 0: crawl(d)
	elif h._headers.type == "application/pdf":
		#print "pdf:", h.geturl()
		savepdf(h)	
	#else:
	#	print "unknown type:", h._headers.type	

def crawl(d):
	links = [ l for l in b.links() ]
	for l in links:
		#print repr(l)
		try:
			h = b.follow_link(l)
			openurl(h, d - 1)
			b.back()
		except:
			pass

openurl(b.open(args[0]), depth)

