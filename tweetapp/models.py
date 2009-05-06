from django.db import models

class TwitterUser(models.Model):
    username = models.CharField(max_length=50)
    lastlogin = models.DateTimeField(null=True)

class FollowPair(models.Model):
    user        = models.ForeignKey(TwitterUser, to_field='username')
    follower    = models.CharField(max_length=50)
    added       = models.DateTimeField(auto_now_add=True)
    removed     = models.DateTimeField(null=True)
