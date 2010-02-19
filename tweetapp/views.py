"""Views for tweetapp"""

from django.shortcuts import render_to_response
from models import TwitterUser, Followers
from django.core.mail import EmailMessage

import twitter

# 'Fake' account to use for all queries
USER = 'glow__worm'
PASS = 'glowworm'


class AlreadyRegistered(Exception):
    """User already registered with local DB"""
    pass


class InvalidTwitterCred(Exception):
    """Twitter credentials are incorrect (user/pass)"""
    pass


def _get_api(user, pwd):
    """Attempt to create an api object for given twitter credentials
        - Raises InvalidTwitterCred if invalid user/pass combo
    """
    api = twitter.Twitter(user, pwd)

    # Verify correct twitter password
    try:
        api.statuses.friends_timeline()
    except twitter.api.TwitterError:
        raise InvalidTwitterCred()

    # Note: Current version of twitter module has bug that will raise
    #       NameError when authentication is wrong
    except:
        raise InvalidTwitterCred()

    return api


def _lookup_twitter_user(user):
    """Look up user from twitter and return dictionary of user
        - See twitter api users/show for info. on return info

        - Raises InvalidTwitterCred if user doesn't exist
    """

    api = _get_api(USER, PASS)

    try:
        user = api.users.show(screen_name=user)

    # Note: Current version of twitter module has bug that will raise
    #       NameError when authentication is wrong
    except:
        raise InvalidTwitterCred()

    return user


def _get_local_user(user, email):
    """Find/create local TwitterUser DB object
        - Raises InvalidTwitterCred if user doesn't exist on twitter's side

        - Raises AlreadyRegistered if user already registered in local DB
    """

    if TwitterUser.objects.filter(username=user):
        raise AlreadyRegistered()

    # Raises exception is user doesn't exist
    twitter_user = _lookup_twitter_user(user)

    local_user = TwitterUser(username=user, email=email)

    # FIXME: Exception to catch?
    local_user.save()

    return local_user


def _get_all_followers(user):
    """Get all the followers for twitter user
        - Raises InvalidTwitterCred if unable to login to query twitter
    """

    # Get api object for query (raises exception if validation fails)
    api = _get_api(USER, PASS)

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


def _update_followers(user):
    """Update the followers for twitter user
        - Raises InvalidTwitterCred if unable to login to query twitter
    """

    # Get current followers (rasies exception if validation fails)
    curr = _get_all_followers(user)

    prev = set()
    db_usr = TwitterUser.objects.filter(username=user)[0]

    for usr in Followers.objects.filter(user=user):
        prev.add(usr.follower)

    added = curr - prev
    removed = prev - curr

    for usr in removed:
        tmp = Followers.objects.filter(follower=usr)
        tmp.delete()

    for usr in added:
        tmp = Followers(user=db_usr, follower=usr)
        tmp.save()

    return (added, removed)


def update_followers(request, user):
    """Handle request for updating followers for given user"""

    try:
        added, removed = _update_followers(user)
    except InvalidTwitterCred:
        return render_to_response('register.html',
                        {'msg': 'Unable to find Twitter User (%s)' % (user)})

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

    return render_to_response('followers.html', {'user': user,
                                        'added': added, 'removed': removed})


def update_all(request):
    """Handle request to update followers for all existing registered users"""

    for user in TwitterUser.objects.all():
        update_followers(request, user.username)

    return render_to_response('register.html')


# FIXME: Change all requests that use POST data to return HttpResponseRedirect
#        (http://docs.djangoproject.com/en/dev/intro/tutorial04/)


def register(request):
    """Handle request for registering new user"""

    if request.method != 'POST':
        return render_to_response('register.html')

    user = request.POST.get('user', '')
    email = request.POST.get('email', '')

    if user == '' or email == '':
        return render_to_response('register.html',
                        {'msg': 'Must enter username/e-mail'})

    try:
        _get_local_user(user, email)
    except AlreadyRegistered:
        return render_to_response('register.html',
                        {'msg': 'Already registered'})
    except InvalidTwitterCred:
        return render_to_response('register.html',
                        {'msg': 'Unable to find Twitter User (%s)' % (user)})

    msg = "Thanks for registering.  Hopefully you'll never get " +\
          "an e-mail from us!"
    return render_to_response('home.html', {'msg': msg})


def users(request):
    """Handle request for displaying all registered users"""

    return render_to_response('users.html',
                                {'users': TwitterUser.objects.all()})
