from django.shortcuts import render_to_response
from tweetapp.models import TwitterUser, Followers
from django.http import HttpResponseRedirect

import datetime
import twitter

class AlreadyRegistered(Exception): pass


def __get_api__(user, pwd):
    # Verify it is the correct twitter password
    api = twitter.Twitter(user, pwd)

    try:
        api.statuses.friends_timeline()
    except twitter.api.TwitterError:
        return None

    return api
 

def __get_twitteruser__(user, email):
    if TwitterUser.objects.filter(username=user):
        raise AlreadyRegistered()

    twitteruser = TwitterUser(username=user, email=email)

    # FIXME: Exception to catch?
    twitteruser.save()

    return twitteruser


def __get_all_followers__(api, user):
    ii = -1
    followers = set()

    while True:
        cur = api.statuses.followers(screen_name=user, cursor=ii)
        if not len(cur['users']):
            break

        for follower in cur['users']:
            followers.add(follower['screen_name'])

        ii = cur['next_cursor']
    return followers


def __update_followers__(user):
    prev = set()
    db_usr = TwitterUser.objects.filter(username=user)[0]

    for usr in Followers.objects.filter(user=user):
        prev.add(usr.follower)

    curr = __get_all_followers__(__get_api__('glow__worm', 'glowworm'), user)

    added = curr - prev
    removed = prev - curr

    for usr in removed:
        tmp = Followers.objects.filter(follower=usr)
        tmp.delete()

    for usr in added:
        tmp = Followers(user=db_usr, follower=usr)
        tmp.save()
        print usr
        
    return (added, removed)

def update_followers(request, user):
    added, removed = __update_followers__(user)

    return render_to_response('followers.html', {'user' : user,
                                        'added' : added, 'removed' : removed})

# FIXME: Change all requests that use POST data to return HttpResponseRedirect
#        (http://docs.djangoproject.com/en/dev/intro/tutorial04/)
def register(request):
    if request.method != 'POST':
        return render_to_response('register.html')

    user = request.POST.get('user', '')
    email = request.POST.get('email', '')

    if user == '' or email == '':
        return render_to_response('register.html',
                        {'msg': 'Must enter username/e-mail'})

    try:
        usr = __get_twitteruser__(user, email)
    except AlreadyRegistered:
        return render_to_response('register.html',
                        {'msg': 'Already registered'})

    return render_to_response('home.html')

def users(request):
    usrs = TwitterUser.objects.all()
    return render_to_response('users.html', {'users' : usrs})
