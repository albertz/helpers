#!/usr/bin/python

import better_exchook
better_exchook.install()
from itertools import *
from pprint import pprint
import os, sys


LastFmUser = "www_az2000_de"
# This key is from the web example...
LastFmApiKey = "29d301e504af323d6246d9c652c227fa"
PageLimit = 200

# http://www.last.fm/api/show/user.getRecentTracks

import webserviceclient
client = webserviceclient.WebServiceClient(api_host="http://ws.audioscrobbler.com/2.0/")

def get(page=1):
	return client.request({
		"api_key": LastFmApiKey,
		"user": LastFmUser,
		"format": "json",
		"method": "user.getRecentTracks",
		"page": page,
		"limit": PageLimit,
		})

mydir = os.path.dirname(__file__)
LogFile = mydir + "/lastfm-history.log"

def loadLog():
	global log
	
	try:
		log = eval(open(LogFile).read())
		assert isinstance(log, dict)
	except IOError: # e.g. file-not-found. that's ok
		log = {}
	except:
		print "logfile reading error"
		sys.excepthook(*sys.exc_info())
		log = {}

def betterRepr(o):
	# the main difference: this one is deterministic
	# the orig dict.__repr__ has the order undefined.
	if isinstance(o, list):
		return "[" + ", ".join(map(betterRepr, o)) + "]"
	if isinstance(o, tuple):
		return "(" + ", ".join(map(betterRepr, o)) + ")"
	if isinstance(o, dict):
		return "{\n" + "".join(map(lambda (k,v): betterRepr(k) + ": " + betterRepr(v) + ",\n", sorted(o.iteritems()))) + "}"
	# fallback
	return repr(o)
	
def saveLog():
	global log, LogFile
	f = open(LogFile, "w")
	f.write(betterRepr(log))
	f.write("\n")

def formatDate(t):
	# if you used an old script which didn't saved the UTC stamp, use this script:
	# https://github.com/albertz/memos/blob/7a19a7cc4a3fcb2f1daebbc45e2da896032704a2/twitter-fixdates.py
	return time.strftime("%Y-%m-%d %H:%M:%S +0000", t)
	
# log is dict: timestamp -> dict for play-event
# play-event dict: artist, title
loadLog()

for page in count(1):
	ret = get(page=page)
	if "error" in ret:
		pprint(ret)
		sys.exit(1)
		
	for retTrack in ret["recenttracks"]["track"]:
		if "date" not in retTrack: continue # probably nowplaying
		timestamp = long(retTrack["date"]["uts"])
		track = log.setdefault(timestamp, {})
		track["artist"] = retTrack["artist"]["#text"]
		track["artist.mbid"] = retTrack["artist"]["mbid"]
		track["title"] = retTrack["name"]
		track["mbid"] = retTrack["mbid"]
		track["timestamp"] = timestamp
		pprint(track)
	saveLog()
	




