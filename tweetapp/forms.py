"""Forms for tweetapp """

from google.appengine.ext.db import djangoforms

from tweetapp.models import TwitterUser


class UserForm(djangoforms.ModelForm):
    """User form"""

    class Meta:
        """Create form from model"""
        model = TwitterUser
