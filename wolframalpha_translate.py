
""" This script is supposed to translate Wolfram Alpha plaintext output
to C syntax code.
Very simple for now and very restricted but works for my (single) usage which is:
http://www.wolframalpha.com/input/?i=solve+a*x_1%5E3+%2B+b*x_1%5E2+%2B+c*x_1+%2B+d+%3D+x_1%2C+3a+*+x_1%5E2+%2B+2b*x_1+%2B+c+%3D+1%2C+a*x_2%5E3+%2B+b*x_2%5E2+%2B+c*x_2+%2B+d+%3D+1%2C+3a*x_2%5E2+%2B+2b*x_2+%2B+c+%3D+0
"""

import sys
from StringIO import StringIO

input = sys.stdin.read()
def out(c): sys.stdout.write(c)

Ops = "+-*/^="

# should remove outer brackets, etc
def baseStrCleanup(s):
	# simple but works for now
	return s.strip("()")

def parse(s, out):
	bracketDepth = 0
	bracketStr = ""
	parts = [""] # expr, op, expr, op, expr, ...
	def subOut(s2):
		parts[-1] += s2
	for c in s:
		if c == ")":
			bracketDepth -= 1
			assert bracketDepth >= 0
			if bracketDepth == 0:
				subOut("(")
				parse(bracketStr, subOut)
				subOut(")")
				bracketStr = ""
				continue
		if bracketDepth > 0:
			bracketStr += c
		if c == "(":
			if bracketDepth == 0:
				if parts[-1]: parts += [""]
			bracketDepth += 1
		if bracketDepth > 0: continue

		if c == "_": continue # make x_1 -> x1
		
		# firt char is always part of an expr
		if not parts[-1]:
			if c == " ": continue # ignore empty
			subOut(c)
			continue
		
		# handle ops. but only if the last part was not an opt (this is the case "1 + -2")
		if c in Ops and parts[-1] not in Ops:
			parts += [c]
			continue
		
		if c == " ":
			parts += [""]
			continue
		
		# last was op, we start an expr now
		if parts[-1] in Ops:
			parts += [""]
		
		subOut(c)

	# now fix ^ op to pow
	while "^" in parts:
		i = parts.index("^")
		assert i > 0
		assert i < len(parts) - 1
		base = baseStrCleanup(parts[i-1])
		exp = baseStrCleanup(parts[i+1])
		parts[i-1:i+2] = ["pow(%s, %s)" % (base, exp)]
	
	# make brackets around "/" usage
	while "/" in parts:
		i = parts.index("/")
		assert i > 0
		assert i < len(parts) - 1
		nom = parts[i-1]
		denom = parts[i+1]
		parts[i-1:i+2] = ["(%s / %s)" % (nom, denom)]

	# make implicit multiplication explicit
	i = 0
	while i < len(parts) - 1:
		if parts[i] not in Ops and parts[i+1] not in Ops:
			parts[i:i+2] = [parts[i], "*", parts[i+1]]
			i += 2
		else:
			i += 1

	#print repr(s), "->", parts	
	out(" ".join(parts))
	
for part in input.split(","):
	part = part.strip()
	parse(part, out)
	out(";\n")
	#print part
	#break


