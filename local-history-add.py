#!/usr/bin/env python3

import os, sys

def get_login_user():
	import pwd, os
	return pwd.getpwuid(os.getuid())[0]

def utc_datetime_str():
	from datetime import datetime
	return datetime.utcnow().strftime("%Y-%m-%d.%H-%M-%S")

def get_history_filename():
	return os.getcwd() + "/.history." + get_login_user()

def is_good_entry(entry):
	entry = entry.strip()
	if not entry: return False # empty
	if entry in ("cd", "ls", "ls -la", "ll"): return False
	return True
	
def add_entry(entry):
	filename = get_history_filename()
	s = utc_datetime_str() + " " + entry + "\n"
	f = open(filename, "a")
	f.write(s)
	f.close()

def maybe_add_entry(entry):
	if not is_good_entry(entry): return
	add_entry(entry)
	
if __name__ == "__main__":
	try:
		maybe_add_entry(" ".join(sys.argv[1:]))
	except IOError as e:
		# Permission denied or so.
		print(e)
