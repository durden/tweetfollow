from django.shortcuts import render_to_response
from tweetapp.models import TwitterUser, FollowPair
from urllib2 import HTTPError
from django.http import HttpResponseRedirect

import datetime
import twitterapi

def __get_api__(user, pwd):
    # Verify it is the correct twitter password
    api = twitterapi.Api(username=user, password=pwd)

    try:
        api.GetUserTimeline()
    # HttpError (401) is raised if bad password
    except (twitterapi.TwitterError, HTTPError):
        return None

    return api
 
def __get_twitteruser__(user):
    if TwitterUser.objects.filter(username=user):
        twitteruser = TwitterUser.objects.get(username=user)

    else:
        twitteruser = TwitterUser(username=user)

        # FIXME: Exception to catch?
        twitteruser.save()

    return twitteruser


#FIXME: It would be nice to pass 1 parameter here (api) and get username
#       from there
def __update_followers__(api, user):
    followers = api.GetFollowers()
    twitteruser = __get_twitteruser__(user)

    # Get followers as last seen by the database
    dbFollowerPairs = FollowPair.objects.filter(user=twitteruser.username,
                                                removed=None)

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
        followpair.user = twitteruser
        followpair.followerid = follower
        followpair.save()

    for follower in removed:
        followpair = FollowPair.objects.filter(user=twitteruser.username,
                                               followerid=follower, removed=None)[0]
        followpair.removed = datetime.datetime.now()
        followpair.save()

    pairs = []

    for followpair in FollowPair.objects.filter(user=twitteruser.username,
                                                removed=None):
        pairs.append(followpair)

    return pairs

def __valid_session__(request):
    if 'user' in request.session and 'pwd' in request.session:
        return True

    return False

# Just a small wrapper for refresh/login to share some more code and passing
# info to the home template
def __show_home__(request, user, pwd):
    # FIXME: This is weird b/c we 'validate' by getting an api instance
    api = __get_api__(user, pwd)
    if api is not None:
        pairs =  __update_followers__(api, user)

        # Check valid session again here b/c we can get here from login
        # and/or refresh
        if not __valid_session__(request):
            request.session['user'] = user
            request.session['pwd'] = pwd

        return render_to_response('home.html', {'followers' : pairs})

    return render_to_response('login.html',
                        {'msg' : 'Twitter user/password incorrect'})

def home(request):
    return render_to_response('home.html')

def refresh(request):
    if __valid_session__(request):
        return __show_home__(request, request.session['user'],
                             request.session['pwd'])

    # Just render login w/o error b/c they probably never logged in
    return render_to_response('login.html')

def logout(request):
    if __valid_session__(request):
        del request.session['user']
        del request.session['pwd']

    return render_to_response('login.html')

# FIXME: Change all requests that use POST data to return HttpResponseRedirect
#        (http://docs.djangoproject.com/en/dev/intro/tutorial04/)
def login(request):
    # If they are already logged in, just refresh
    if __valid_session__(request):
        return HttpResponseRedirect('/refresh')

    if request.method != 'POST':
        return render_to_response('login.html')

    user = request.POST.get('user', '')
    pwd = request.POST.get('pwd', '')

    if user == '' or pwd == '':
        return render_to_response('login.html',
                        {'msg': 'Must enter user and pwd'})

    return __show_home__(request, user, pwd)

def users(request):
    usrs = TwitterUser.objects.all()
    return render_to_response('users.html', {'users' : usrs})
