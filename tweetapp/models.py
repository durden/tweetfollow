from appengine_django.models import BaseModel
from google.appengine.ext import db

class TwitterUser(BaseModel):
    username = db.StringProperty()
    email = db.EmailProperty()

class Followers(BaseModel):
    user        = db.ReferenceProperty(TwitterUser)
    follower    = db.StringProperty()
