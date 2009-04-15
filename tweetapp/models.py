from django.db import models

#FIXME: Some notable problems with this implementation:
#		1. We can't detect ALL follower changes (specific users, etc), only changes in the overall
#		   follower count trigger a 'save'.

class TwitterUser(models.Model):
    username = models.CharField(max_length=50)
    last_visited = models.DateTimeField(auto_now=True)
    follow_count = models.IntegerField()

class FollowerChange(models.Model):
    user = models.ForeignKey(TwitterUser, to_field='username')
    type = models.BooleanField()
    time = models.DateTimeField(auto_now=True)
    count = models.IntegerField()

    # Store tweets here b/c doesn't seem like a reason to just retrieve the tweets without
    # the follower change
    tweet1 = models.CharField(max_length=140)
    tweet2 = models.CharField(max_length=140)
    tweet3 = models.CharField(max_length=140)
    tweet4 = models.CharField(max_length=140)
    tweet5 = models.CharField(max_length=140)
    # FIXME: Maybe find an actual list type?
    # FIXME: Store the usernames of followers

class FollowPair(models.Model):
	user        = models.ForeignKey(TwitterUser, to_field='username')
	followerid  = models.IntegerField()
	start       = models.DateTimeField(auto_now=True)
	stop        = models.DateTimeField(auto_now=True)
