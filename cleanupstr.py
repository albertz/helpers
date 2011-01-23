# string cleanup functions
# by Albert Zeyer
# code under zlib

def cleanupstr(s):
	ret = ""
	for c in s:
		if ord(c) < 32: continue
		ret += c
	return ret
