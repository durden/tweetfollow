from django.shortcuts import render_to_response
from tweetapp.models import TwitterUser, FollowPair
from urllib2 import HTTPError

import datetime
import twitterapi

def home(request):
    return render_to_response('home.html')

def login(request):
    if request.method != 'POST':
        return render_to_response('login.html')

    user = request.POST.get('user', '')
    pwd = request.POST.get('pwd', '')

    if user == '' or pwd == '':
        return render_to_response('login.html',
                        {'msg': 'Must enter user and pwd'})

    # Verify it is the correct twitter password
    api = twitterapi.Api(username=user, password=pwd)

    try:
        api.GetUserTimeline()
    # HttpError (401) is raised if bad password
    except (twitterapi.TwitterError, HTTPError):
        return render_to_response('login.html',
                        {'msg' : 'Twitter user/password incorrect'})

    user_obj = None
    followers = api.GetFollowers()
    cnt = len(followers)

    # Update last_visited and follower_count
    if TwitterUser.objects.filter(username=user):
        user_obj = TwitterUser.objects.get(username=user)

    else:
        user_obj = TwitterUser(username=user)

    user_obj.follow_count = cnt

    # FIXME: Exception to catch?
    user_obj.save()

    # Get followers as last seen by the database
    dbFollowerPairs = FollowPair.objects.filter(user=user_obj.username, removed=None)

    dbFollowerIds = set()
    for pair in dbFollowerPairs:
        dbFollowerIds.add(int(pair.followerid))
    
    curFollowerIds = set()
    for follower in followers:
        curFollowerIds.add(int(follower.id))

    # Compare database's set of followers to the current
    added   = curFollowerIds - dbFollowerIds
    removed = dbFollowerIds  - curFollowerIds

    for follower in added:
        followpair = FollowPair()
        followpair.user = user_obj
        followpair.followerid = follower
        followpair.save()

    for follower in removed:
        followpair = FollowPair.objects.filter(user=user_obj.username,
                                               followerid=follower, removed=None)[0]
        followpair.removed = datetime.datetime.now()
        followpair.save()

    pairs = []
    for followpair in FollowPair.objects.filter(user=user_obj.username, removed=None):
        pairs.append(followpair)

    return render_to_response('home.html', {'followers' : pairs})

def users(request):
    usrs = User.objects.all()
    return render_to_response('users.html', {'users' : usrs})
