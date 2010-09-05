"""Views for tweetapp"""

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.mail import EmailMessage

from django.utils import simplejson

from google.appengine.ext import db

import urllib2

from tweetapp.models import TwitterUser, Followers
from tweetapp.forms import UserForm


class AlreadyRegistered(Exception):
    """User already registered with local DB"""
    pass


class InvalidTwitterCred(Exception):
    """Twitter credentials are incorrect (user/pass)"""
    pass


class MissingLocalUser(Exception):
    """User doesn't exist in local DB"""
    pass


class Twitter(object):
    """Simple wrapper class for twitter api via json"""

    def followers(self, username):
        """Get followers from twitter for given username"""
        # Use -1 to indicate via twitter api that we're starting pagination
        ii = -1
        followers = []

        # api returns 0 for cursor when no more pages exist
        while ii != 0:
            url = ''.join(['http://api.twitter.com/1/statuses/followers.json',
                            '?screen_name=%s' % (username), '&cursor=%d' % (ii)])

            # Deliberately DON'T catch http exception b/c caller will
            # interpret this as the credentials being incorrect if it fails
            json = simplejson.loads(urllib2.urlopen(url).read())

            ii = json['next_cursor']

            for user in json['users']:
                followers.append(user['screen_name'])


def _get_api():
    """Create api instance to use
        - Method only exists to hopefully try to hide what twitter library is
          being used
    """
    return Twitter()


def _lookup_twitter_user(user):
    """Look up user from twitter
        - Raises InvalidTwitterCred if user doesn't exist
        - No return value
    """

    api = _get_api()

    # Try to see the user's followers, assume any problem means
    # the user doesn't exist b/c we are cheating and not going to
    # bother with users that are set to private, etc.
    try:
        api.followers(user)
    except:
        raise InvalidTwitterCred()


def _create_local_user(username, email):
    """Find/create local TwitterUser DB object
        - Raises InvalidTwitterCred if user doesn't exist on twitter's side

        - Raises AlreadyRegistered if user already registered in local DB
    """

    if TwitterUser.all().filter("username = ", username).count():
        raise AlreadyRegistered()

    # Raises exception is user doesn't exist
    _lookup_twitter_user(username)

    local_user = TwitterUser(username=username, email=email)
    db.put(local_user)

    return local_user


def _get_current_followers(username):
    """Get all the current followers for twitter user from twitter api
        - Raises InvalidTwitterCred if unable to login to query twitter
    """

    # Get api object for query (raises exception if validation fails)
    api = _get_api()

    ii = -1
    followers = set()

    while True:
        cur = api.statuses.followers(screen_name=username, cursor=ii)
        if not len(cur['users']):
            break

        for follower in cur['users']:
            followers.add(follower['screen_name'])

        ii = cur['next_cursor']

    return followers


def _get_previous_followers(user):
    """Get all the previous followers for twitter user from from local DB
        - Argument is of type local model -- TwitterUser
    """

    followers = set()

    for usr in Followers.all().filter("user = ", user.key()):
        followers.add(usr.follower)

    return followers


def _update_followers(username):
    """Update the followers for twitter user
        - Raises InvalidTwitterCred if unable to login to query twitter

        - Raises MissingLocalUser if user doesn't exist in local DB
    """

    # Verify user exists locally
    try:
        db_user = TwitterUser.all().filter("username = ", username)[0]
    except IndexError:
        raise MissingLocalUser()

    # Current followers (raises exception if twitter doesn't find user)
    curr = _get_current_followers(username)

    # Current followers (raises exception if user doesn't exist locally)
    prev = _get_previous_followers(db_user)

    added = curr - prev
    removed = prev - curr

    for usr in removed:
        tmp = Followers.all().filter("follower =", usr)
        db.delete(tmp)

    for usr in added:
        tmp = Followers(user=db_user, follower=usr)
        db.put(tmp)

    return (added, removed)


def _send_email(lost, user):
    """Generate and send e-mail for lost followers"""

    if lost and len(lost):
        body = "<p>The following users recently un-followed you:</p><ul>"

        for usr in lost:
            body += '<li><a href="http://www.twitter.com/%s">%s</a></li>' % (usr, usr)

        body += "</ul>"

        msg = EmailMessage("TweetFollow: Lost %d followers" % (len(lost)),
                        body, 'follow@tweetfollow.durden.webfactional.com',
                        [user.email])
        msg.content_subtype = 'html'
        msg.send()


def update_followers(request, username):
    """Handle request for updating followers for given user"""

    try:
        added, removed = _update_followers(username)
    except InvalidTwitterCred:
        return render_to_response('register.html',
                    {'msg': 'Unable to find Twitter User (%s)' % (username)})
    except MissingLocalUser:
        return render_to_response('register.html',
                    {'msg': 'Please register user (%s) first' % (username)})

    # Send e-mail to local user
   db_user = TwitterUser.all().filter("username = ", username)[0]
    _send_email(removed, db_user)

    return render_to_response('followers.html', {'user': username,
                                        'added': added, 'removed': removed})


def update_all(request):
    """Handle request to update followers for all existing registered users"""

   for user in TwitterUser.all():
        update_followers(request, user.username)

    return render_to_response('register.html')


def register(request):
    """Handle request for registering new user"""

    if request.method != 'POST':
        return render_to_response('register.html')

    # Use form for e-mail validation
    form = UserForm(request.POST)

    if not form.is_valid():
        return render_to_response('register.html',
                        {'msg': 'Must enter valid username/e-mail'})

    name = form.cleaned_data['username']
    email = form.cleaned_data['email']

    # Verify twitter thinks user exists and create/get local user
    try:
        _create_local_user(name, email)
    except AlreadyRegistered:
        return render_to_response('register.html',
                        {'msg': 'Already registered'})
    except InvalidTwitterCred:
        return render_to_response('register.html',
                        {'msg': 'Unable to find Twitter User (%s)' % (name)})

    return HttpResponseRedirect('/success/')


def users(request):
    """Handle request for displaying all registered users"""

    return render_to_response('users.html',
                               {'users': TwitterUser.all()})
