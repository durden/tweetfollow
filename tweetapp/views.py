from django.shortcuts import render_to_response
from tweetapp.models import TwitterUser, FollowerChange, FollowPair
from urllib2 import HTTPError

import twitterapi

def home(request):
	return render_to_response('home.html')

def login(request):
	if request.method == 'POST':
		user = request.POST.get('user', '')
		pwd = request.POST.get('pwd', '')

		if user == '' or pwd == '':
			return render_to_response('login.html', {'msg': 'Must enter user and pwd'})

		# Verify it is the correct twitter password
		api = twitterapi.Api(username=user, password=pwd)

		try:
			api.GetUserTimeline()
		# HttpError (401) is raised if bad password
		except (twitterapi.TwitterError, HTTPError):
			return render_to_response('login.html', {'msg' : 'Twitter user/password incorrect'})

		user_obj = None
		change_obj = None
		followers = api.GetFollowers()
		cnt = len(followers)

		# Update last_visited and follower_count
		if TwitterUser.objects.filter(username=user):
			user_obj = TwitterUser.objects.get(username=user)

			#FIXME: update last_visited
			if cnt != user_obj.follow_count:
				change_obj = FollowerChange()	
				change_obj.user = user_obj

				# FIXME Probably some cool python trick to do this in 1 line
				recent_tweets = api.GetUserTimeline(count=5)
				change_obj.tweet1 = recent_tweets[0].text
				change_obj.tweet2 = recent_tweets[1].text
				change_obj.tweet3 = recent_tweets[2].text
				change_obj.tweet4 = recent_tweets[3].text
				change_obj.tweet5 = recent_tweets[4].text

				follow_diff = user_obj.follow_count - cnt
				change_obj.count = abs(follow_diff)

				# Gained followers
				if follow_diff >= 1:
					change_obj.type = True
				else:
					change_obj.type = False

				# FIXME: exception?
				change_obj.save()
		else:
			user_obj = TwitterUser(username=user)

		user_obj.follow_count = cnt

		# FIXME: Exception to catch?
		user_obj.save()
		
		# save followers
		for follower in followers:
			followpair = FollowPair()
			followpair.user = TwitterUser(username=user)
			followpair.followerid = follower.id
			followpair.save()
		
		return render_to_response('home.html', {'user' : user_obj, 'follow' : change_obj})

	return render_to_response('login.html')

def users(request):
	usrs = User.objects.all()
	return render_to_response('users.html', {'users' : usrs})
