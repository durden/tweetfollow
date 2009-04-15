from django.db import models

#FIXME: Some notable problems with this implementation:
#		1. We can't detect ALL follower changes (specific users, etc), only changes in the overall
#		   follower count trigger a 'save'.

class TwitterUser(models.Model):
    username = models.CharField(max_length=50)
    last_visited = models.DateTimeField(auto_now=True)
    follow_count = models.IntegerField()

class FollowPair(models.Model):
	user        = models.ForeignKey(TwitterUser, to_field='username')
	followerid  = models.IntegerField()
	start       = models.DateTimeField(auto_now=True)
	stop        = models.DateTimeField(auto_now=True)
