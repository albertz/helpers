#!/usr/bin/env python3

import os, sys

login_user = None

def get_login_user():
	if login_user:
		return login_user
	import pwd, os
	return pwd.getpwuid(os.getuid())[0]

def utc_datetime_str():
	from datetime import datetime
	return datetime.utcnow().strftime("%Y-%m-%d.%H-%M-%S")

def get_history_filename():
	return os.getcwd() + "/.history." + get_login_user()

def is_good_entry(entry):
	entry = entry.strip()
	if not entry:
		return False  # empty
	if entry in ("cd", "ls", "ls -la", "ll"):
		return False
	return True

def add_entry(entry):
	filename = get_history_filename()
	s = utc_datetime_str() + " " + entry + "\n"
	f = open(filename, "a")
	f.write(s)
	f.close()

def maybe_add_entry(entry):
	if not is_good_entry(entry):
		return
	add_entry(entry)

def main():
	global login_user
	import argparse
	arg_parser = argparse.ArgumentParser()
	arg_parser.add_argument("text")
	arg_parser.add_argument("--user")
	args = arg_parser.parse_args()
	if args.user:
		login_user = args.user
	try:
		maybe_add_entry(args.text)
	except IOError as e:
		pass


if __name__ == "__main__":
	main()
