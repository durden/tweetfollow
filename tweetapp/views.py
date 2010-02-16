from django.shortcuts import render_to_response
from models import TwitterUser, Followers
from django.http import HttpResponseRedirect
from django.core.mail import EmailMessage

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

    if removed:
        db_usr = TwitterUser.objects.filter(username=user)[0]
        if db_usr.email != "" and len(removed):
            body = "<p>The following users recently un-followed you:</p><ul>"
            for usr in removed:
                body += '<li><a href="http://www.twitter.com/%s">%s</a></li>' % (usr, usr)

            body += "</ul>"

            msg = EmailMessage("TweetFollow: Lost %d followers" % (len(removed)),
                            body, 'follow@tweetfollow.durden.webfactional.com',
                            [db_usr.email])
            msg.content_subtype = 'html'
            msg.send()

    return render_to_response('followers.html', {'user' : user,
                                        'added' : added, 'removed' : removed})

def update_all(request):
    for user in TwitterUser.objects.all():
        update_followers(request, user.username)

    return render_to_response('register.html')

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

    # FIXME: Validate the email is the one associated with the twitter user
    # FIXME: Verify twitter user exists

    try:
        usr = __get_twitteruser__(user, email)
    except AlreadyRegistered:
        return render_to_response('register.html',
                        {'msg': 'Already registered'})

    msg = "Thanks for registering.  Hopefully you'll never get an e-mail from us!"
    return render_to_response('home.html', {'msg' : msg})

def users(request):
    usrs = TwitterUser.objects.all()
    return render_to_response('users.html', {'users' : usrs})
