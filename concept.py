#!/usr/bin/python

import time
import sys
import getpass
import twitterapi

#TODO: Send an email to the account that is associated with the user
#	   who started the script.

if len(sys.argv) <= 1:
	sys.exit("Please specify your twitter username")

user = sys.argv[1]
pwd = getpass.getpass()

if len(pwd) == 0:
	sys.exit("Please specify your twitter password")

api = twitterapi.Api(username=user, password=pwd)

try:
	while 1:
		followers1 = set(api.GetFollowers())

		if not len(followers1):
			print "You don't have any friends yet?!"

		# FIXME: Sleep will have to be much longer if you want to run
        #		 this for longer than a few minutes.
		time.sleep(30)
	
		followers2 = set(api.GetFollowers())

		if len(followers1) > len(followers2):
			missing = followers1 - followers2

			for usr in missing:
				print usr.name, " hates you now"

			print "What you said to piss them off:"
			# FIXME: This just gets the last 20 tweets probably want
			#		 get the ones since the first followers were found
			tweets = api.GetUserTimeline()
			for tweet in tweets:
				print tweet.created_at, " -- ", tweet.text

except KeyboardInterrupt:
	pass
