from django.shortcuts import render_to_response
from tweetapp.models import TwitterUser, FollowerChange
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

		user_obj = TwitterUser(username=user)

		# FIXME: Exception to catch?
		user_obj.save()

		return render_to_response('login.html', {'msg' : 'Added %s!' % (user)})

	return render_to_response('login.html')

def users(request):
	usrs = User.objects.all()
	return render_to_response('users.html', {'users' : usrs})
