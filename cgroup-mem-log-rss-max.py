#!/usr/bin/env python3

"""
This script uses the informations from cgroup to log the rss memory usage of the given job.
Originally written by Jan-Thorsten Peter, modified by Albert Zeyer.
"""

import sys, os, time

def byteNumRepr(c):
	if c < 1024: return "%i B" % c
	S = "KMG"
	i = 0
	while i < len(S) - 1:
		if c < 0.8 * 1024 ** (i + 2): break
		i += 1
	f = float(c) / (1024 ** (i + 1))
	return "%.1f %sB" % (f, S[i])

class RssChecker(object):
	def __init__(self, stat_file):
		self.stat_file = stat_file
		self.max_value = 0

	def get_rss(self):
		stats = open(self.stat_file).read().splitlines()
		stats = dict([(key,int(value)) for key,value in map(str.split, stats)])
		return stats["rss"]

	def update(self):
		value = self.get_rss()
		if value > self.max_value:
			self.max_value = value
			print("New maximum RSS usage: %s" % byteNumRepr(value))

def main():
	# cgroups path to memory statistic file
	stat_file = '/sys/fs/cgroup/memory/memory.stat'

	checker = RssChecker(stat_file)
	while os.getppid() > 1: # run while parent process exists
		checker.update()
		time.sleep(1)

if __name__ == '__main__':
	main()
