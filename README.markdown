About
========

Simple django project to allow twitter users to get automatic e-mail updates when
they lose followers.

The app only requires that users enter their twitter username and an e-mail to
receive updates.

There is a dedicated 'hidden' user that does all the authenticated calls to the
twitter API.  This allows users to register without providing their twitter
password.  It also allows me to not worry about implementing Open ID :)

Lots of features hopefully to be added and it is not stable yet.

Requirements
--------

Currently using [twitter api](http://github.com/sixohsix/twitter)

I started this project by using the
[python-twitter api](http://code.google.com/p/python-twitter/).  Specifically,
I was using the [github fork] (http://github.com/idangazit/python-twitter/tree/master).

The python-twitter api is really great and used all around the Internet for
python projects.  However, it currently only allowed for fetching 100 followers
due to how it interacts with the twitter API.  The twitter API does allow you
to fetch all followers, but this requires multiple requests and an index.

Ultimately, the twitter api maintained by [Mike Verdone](http://mike.verdone.ca)
allowed me to easily retrieve all followers.
