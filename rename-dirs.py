#!/usr/bin/python
# -*- coding: utf8 -*-

# Simple pic directory renamer script.
# by Albert Zeyer
# code under zlib

# Adds a date (eg. "2011_01_22__") as a prefix to each dir.
# Asks for confirmation, so it is safe to just try out and see what it would do.


import sys, os
import better_exchook
better_exchook.install()

def usage(): print "usage:", sys.argv[0], "<dir>"
	
if len(sys.argv) != 2:
	usage()
	quit()

dir = sys.argv[1]
if not os.path.isdir(dir):
	print dir, "is not a directory"
	usage()
	quit()

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

def find_date_str(f):
	f = os.path.basename(f)
	p = f.rfind("(")
	if p < 0: return None
	if f[-1] != ")": return None
	return f[p+1:-1]

dateReplaceMap = {
	"januar": 1,
	"februar": 2,
	"maerz": 3,
	u"märz": 3,
	"april": 4,
	"mai": 5,
	"juni": 6,
	"juli": 7,
	"august": 8,
	"september": 9,
	"oktober": 10,
	"november": 11,
	"dezember": 12,
}

def parse_date(date_str):
	date_str = date_str.replace(" ", "")
	date_str = date_str.lower()
	for k,v in dateReplaceMap.items():
		date_str = date_str.replace(k, str(v) + ".")
	for c in date_str:
		if c not in "0123456789.": return None
	date = date_str.split(".")
	date += ["",""]
	year = int(date[2]) if date[2] else None
	month = int(date[1]) if date[1] else None
	day = int(date[0]) if date[0] else None
	return [year,month,day]

assert parse_date("26. 12. ") == [None,12,26]
assert parse_date(" 30. 12. 2004") == [2004,12,30]
assert parse_date("15") == [None,None,15]
assert parse_date(u'19. März 2007') == [2007,3,19]

def parse_date_range(date_str):
	p = date_str.find("-")
	if p >= 0:
		start = parse_date(date_str[:p])
		end = parse_date(date_str[p+1:])
		if not start: return None
		if not start[2]: return None
		if not end: return None
		if not all(end): return None
		if not start[0]: start[0] = end[0]
		if not start[1]: start[1] = end[1]
	else:
		start = parse_date(date_str)
		end = None
	return start,end

assert parse_date_range("26. 12. - 30. 12. 2004") == ([2004,12,26],[2004,12,30])
assert parse_date_range(u'6. - 24. Juli 2005') == ([2005,7,6],[2005,7,24])
assert parse_date_range(u'13. August - 28. August 2004') ==  ([2004,8,13],[2004,8,28])
assert parse_date_range(u'19. März 2007') == ([2007,3,19],None)
assert parse_date_range(u'15 - 19. März 2007') == ([2007,3,15],[2007,3,19])
 
def format_date_str(date):
	year,month,day = date
	if year < 50: year += 2000
	if year < 100: year += 1900
	return "%04i_%02i_%02i" % (year,month,day)

def normalize_basename(f):
	f = f.strip()
	f = f.lower()
	f = f.replace(" ", "_")
	return f

files = {}
errors = {}

for f in os.listdir(dir):
	f = f.decode("utf8")
	f = dir + "/" + f
	if not os.path.isdir(f): continue
	try:
		date_str = find_date_str(f)
		if not date_str: continue
		newbasefn = os.path.basename(f)
		newbasefn = newbasefn.replace("(" + date_str + ")", "")
		newbasefn = normalize_basename(newbasefn)
		start,end = parse_date_range(date_str)
		if end:
			prefix = format_date_str(start) + "_-_" + format_date_str(end)
		else:
			prefix = format_date_str(start)
		prefix += "__"
		newfn = os.path.dirname(f) + "/" + prefix + newbasefn
		if os.path.exists(newfn):
			errors[f] = os.path.basename(newfn) + " already exists"
		elif os.path.basename(f)[0:len(prefix)] == prefix:
			errors[f] = os.path.basename(f) + " already has the prefix '" + prefix + "'"			
		else:
			files[f] = newfn
	except Exception, e:
		errors[f] = str(e)
		sys.excepthook(*sys.exc_info())

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

