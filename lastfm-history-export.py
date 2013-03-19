#!/usr/bin/python

import better_exchook
better_exchook.install()
from itertools import *
from pprint import pprint
import os, sys, time, types


LastFmUser = "www_az2000_de"
StopOnOldEntry = True
PageLimit = 50

# This key is from the web example...
LastFmApiKey = "29d301e504af323d6246d9c652c227fa"

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
	except Exception:
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
	s = betterRepr(log) + "\n"
	f = open(LogFile, "w")
	f.write(s)

def formatDate(t):
	if isinstance(t, (types.IntType,types.LongType,types.FloatType)):
		t = time.gmtime(t)
	return time.strftime("%Y-%m-%d %H:%M:%S +0000", t)
	
# log is dict: timestamp -> dict for play-event
# play-event dict: artist, title
loadLog()


page = 1
while True:
	ret = get(page=page)
	if "error" in ret:
		pprint(ret)
		if int(ret["error"]) == 29: # Rate limit exceeded
			time.sleep(10) # wait a bit
			continue
		sys.exit(1)
	
	for retTrack in ret["recenttracks"]["track"]:
		if "date" not in retTrack: continue # probably nowplaying
		timestamp = long(retTrack["date"]["uts"])
		print "page:", page, ", date:", formatDate(timestamp)
		if StopOnOldEntry and timestamp in log:
			print "This is an old entry:", log[timestamp]
			pprint(retTrack)
			saveLog()
			sys.exit()
		track = {}
		track["artist"] = retTrack["artist"]["#text"]
		track["artist.mbid"] = retTrack["artist"]["mbid"]
		track["title"] = retTrack["name"]
		track["mbid"] = retTrack["mbid"]
		track["timestamp"] = timestamp
		log.setdefault(timestamp, {}).update(track)
		pprint(log[timestamp])
	saveLog()
	
	page += 1



