from django.db import models

class TwitterUser(models.Model):
    username = models.CharField(max_length=50)

class Followers(models.Model):
    user        = models.ForeignKey(TwitterUser, to_field='username')
    follower    = models.CharField(max_length=50)
