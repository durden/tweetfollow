from appengine_django.models import BaseModel
from google.appengine.ext import db


class TwitterUser(BaseModel):
    username = db.StringProperty(required=True)
    email = db.EmailProperty(required=True)
    oauth_secret = db.StringProperty()
    oauth_token = db.StringProperty()


class Followers(BaseModel):
    user = db.ReferenceProperty(TwitterUser)
    follower = db.StringProperty(required=True)
