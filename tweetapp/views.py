"""Views for tweetapp"""

from django.http import HttpResponseRedirect

from django.shortcuts import render_to_response, redirect

from django.utils import simplejson

from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.api.mail import EmailMessage

from tweetapp.models import TwitterUser, Followers
from tweetapp.forms import UserForm

import oauth


CONSUMER_KEY = "GfR48qbxGItXTE1YrX1NvQ"
CONSUMER_SECRET = "hp9odY6zCKSMarAWD6t0eXGA10IslEJeti3MVYAjA"
CALLBACK_URL = "http://lostfollowers.appspot.com/callback/"


def chunk(l, chunksize):
    for i in range(0, len(l), chunksize):
        yield l[i:i+chunksize]


class AlreadyRegistered(Exception):
    """User already registered with local DB"""
    pass


class MissingLocalUser(Exception):
    """User doesn't exist in local DB"""
    pass


class Twitter(object):
    """Simple wrapper class for twitter api via json"""

    def __init__(self, username):
        try:
            self.user = TwitterUser.all().filter("username = ", username)[0]
        except IndexError:
            self.user = None

    def followers(self):
        """Get followers from twitter for given username"""

        # Use -1 to indicate via twitter api that we're starting pagination
        ii = -1
        followers = []

        # api returns 0 for cursor when no more pages exist
        while ii != 0:
            url = ''.join(['http://api.twitter.com/1/followers/ids.json',
                            '?screen_name=%s' % (self.user.username),
                            '&cursor=%d&stringify_ids=true' % (ii)])

            client = oauth.TwitterClient(CONSUMER_KEY, CONSUMER_SECRET,
                                         CALLBACK_URL)
            result = client.make_request(url, token=self.user.oauth_token,
                                        secret=self.user.oauth_secret,
                                        additional_params=None, protected=True,
                                        method=urlfetch.GET)

            if result.status_code != 200:
                raise Exception('Status %d returned %s' % \
                                (result.status_code, result.content))

            json = simplejson.loads(result.content)

            # Twitter API doesn't guarantee how many entires will come back in
            # the request and depending on how many followers user has it might
            # bring all them back at once w/o a cursor
            try:
                ii = json['next_cursor']
            except IndexError:
                ii = 0

            for id in json['ids']:
                followers.append(str(id))

        return self._names_from_ids(followers)


    def _names_from_ids(self, follower_ids):
        """Return set of follower names given a set of follower ids"""

        names = set()

        for ids in chunk(follower_ids, 100):
            url = ''.join(['http://api.twitter.com/1/users/lookup.json',
                            '?user_id=%s' % (','.join(ids))])

            client = oauth.TwitterClient(CONSUMER_KEY, CONSUMER_SECRET,
                                            CALLBACK_URL)
            result = client.make_request(url, token=self.user.oauth_token,
                                        secret=self.user.oauth_secret,
                                        additional_params=None, protected=True,
                                        method=urlfetch.GET)

            if result.status_code != 200:
                raise Exception('Status %d returned %s' % \
                                (result.status_code, result.content))

            json = simplejson.loads(result.content)
            for follower in json:
                names.add(follower['screen_name'])

        return names


def callback(request):
    """Handle oauth callback from twitter"""

    client = oauth.TwitterClient(CONSUMER_KEY, CONSUMER_SECRET, CALLBACK_URL)
    auth_token = request.GET['oauth_token']
    auth_verifier = request.GET['oauth_verifier']
    user_info = client.get_user_info(auth_token, auth_verifier=auth_verifier)

    try:
        user = TwitterUser.all().filter("username = ",
                                        user_info['username'])[0]
    except IndexError:
        return render_to_response('register.html',
                {'msg': 'Please register user (%s) first' % (user.username)})

    user.oauth_secret = user_info['secret']
    user.oauth_token = user_info['token']
    db.put(user)

    return HttpResponseRedirect('/success/')


def _create_local_user(username, email):
    """Find/create local TwitterUser DB object
        - Raises AlreadyRegistered if user already registered in local DB
    """

    if TwitterUser.all().filter("username = ", username).count():
        raise AlreadyRegistered()

    local_user = TwitterUser(username=username, email=email)
    db.put(local_user)

    return local_user


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
        - Raises MissingLocalUser if user doesn't exist in local DB
    """

    # Verify user exists locally
    try:
        db_user = TwitterUser.all().filter("username = ", username)[0]
    except IndexError:
        raise MissingLocalUser()

    # Current followers
    curr = Twitter(username).followers()
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

        msg = EmailMessage(
                        subject="TweetFollow: Lost %d followers" % (len(lost)),
                        html=body,
                        sender="lostfollowers.tweetfollow@gmail.com",
                        to=[user.email])
        msg.send()


def update_followers(request, username):
    """Handle request for updating followers for given user"""

    try:
        added, removed = _update_followers(username)
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


def show_followers(request, username):
    """
    Test view just to verify that the main flow of querying Twitter for
    followers, etc. is working
    """

    # Verify user exists locally
    try:
        db_user = TwitterUser.all().filter("username = ", username)[0]
    except IndexError:
        return render_to_response('register.html',
                    {'msg': 'Please register user (%s) first' % (username)})

    # Current followers
    added = Twitter(username).followers()
    return render_to_response('followers.html', {'user': username,
                                        'added': added, 'removed': None})


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

    # oauth dance, which ends up at the callback url
    client = oauth.TwitterClient(CONSUMER_KEY, CONSUMER_SECRET, CALLBACK_URL)
    return redirect(client.get_authorization_url())


def users(request):
    """Handle request for displaying all registered users"""

    return render_to_response('users.html',
                               {'users': TwitterUser.all()})
