# string cleanup functions
# by Albert Zeyer
# code under zlib

def cleanupstr(s):
	if isinstance(s, str):
		s = bytes(s)
	assert isinstance(s, bytes)
	ret = ""
	for c in s:
		if c < 32: continue
		ret += chr(c)
	return ret
