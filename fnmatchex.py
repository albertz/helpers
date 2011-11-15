# extended fnmatch
# by Albert Zeyer
# code under zlib

# examples:
#   *.[mM][pP]3  # [] just as in regexp. * and ? as usual
#   *.{jpg,jpeg} # {} gives multiple alternatives

import re

def fnpattern_to_re(pattern):
	ret = ""
	state = 0
	for c in pattern:
		if state == 0: # default
			if c == "[": state = 1
			elif c == ",": c = "|"
			elif c == "|": c = "\\|"
			elif c == "*": c = ".*"
			elif c == "?": c = "."
			elif c == ".": c = "\\."
			elif c == "\\": state,oldstate = 2,0
			elif c == "(": c = "\\("
			elif c == ")": c = "\\)"
			elif c == "{": c = "("
			elif c == "}": c = ")"
			ret += c
		elif state == 1: # in "[]"
			if c == "]": state = 0
			elif c == "\\": state,oldstate = 2,1
			ret += c
		elif state == 2: # \-escaped
			ret += c
			state = oldstate
		else:
			raise Exception("bad state: " + str(state))
	return "^(" + ret + ")$"
	
def fnmatchex(filename, pattern):
	return bool(re.match(fnpattern_to_re(pattern), filename))
