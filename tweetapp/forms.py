"""Forms for tweetapp """

from django.forms import ModelForm

from tweetapp.models import TwitterUser

class UserForm(ModelForm):
    """User form"""

    class Meta:
        """Create form from model"""
        model = TwitterUser
