"""Tests for tweetapp application

    The following code tests the majority of the tweetapp request handlers and
    internal helper functions.

    I haven't figured out a good way to test the update* urls yet because
    they depend heavily on the twitter api and constantly changing twitter
    followers, etc.  I can probably mock the twitter api somehow, but no good
    solution yet.
"""

from django.test import TestCase
from django.test.client import Client

from tweetapp.models import TwitterUser
from tweetapp import views


TEST_EMAIL = 'test@test.com'


class RequestTests(TestCase):
    """Class of tests for tweetapp request handlers"""

    def setUp(self):
        """Create django test client for all tests"""
        self.client = Client()

    def tearDown(self):
        """Remove any local DB users created in testing"""

        for user in TwitterUser.objects.all():
            user.delete()

    def test_register_req_success(self):
        """Successful register attempt"""

        name = 'durden20'

        response = self.client.post('/register/', {'username': name,
                                                    'email': TEST_EMAIL})

        # Check that the response is 200 OK.
        self.failUnlessEqual(response.status_code, 200)

        # Should go to home
        self.assertTemplateUsed(response, 'home.html')

        # Verify user in local DB
        users = TwitterUser.objects.all()
        self.failUnlessEqual(len(users), 1)
        self.failUnlessEqual(users[0].email, TEST_EMAIL)
        self.failUnlessEqual(users[0].username, name)

    def test_register_req_missing_user_arg(self):
        """Register fails with no user specified"""
        response = self.client.post('/register/', {'email': TEST_EMAIL})

        # Check that the response is 200 OK.
        self.failUnlessEqual(response.status_code, 200)

        # Should go to register with failure msg
        self.assertTemplateUsed(response, 'register.html')
        self.assertContains(response, 'Must enter username/e-mail')

    def test_register_req_missing_email_arg(self):
        """Register fails with no user specified"""
        response = self.client.post('/register/', {'username': 'user'})

        # Check that the response is 200 OK.
        self.failUnlessEqual(response.status_code, 200)

        # Should go to register with failure msg
        self.assertTemplateUsed(response, 'register.html')
        self.assertContains(response, 'Must enter username/e-mail')

    def test_register_req_invalid_twitter_user(self):
        """Register fails if user doesn't exist on twitter"""

        name = 'baduser123321'
        response = self.client.post('/register/', {'username': name,
                                                    'email': TEST_EMAIL})

        self.assertTemplateUsed(response, 'register.html')
        self.assertContains(response,
                                'Unable to find Twitter User (%s)' % (name))

    def test_register_req_already_registered(self):
        """Register fails is user already registered"""

        # Add user
        user = TwitterUser(username=views.USER, email=TEST_EMAIL)
        user.save()

        # Register again
        response = self.client.post('/register/', {'username': user.username,
                                                    'email': user.email})

        self.assertTemplateUsed(response, 'register.html')
        self.assertContains(response, 'Already registered')

    def test_register_req_invalid_email(self):
        """Register fails with invalid e-mail"""

        response = self.client.post('/register/', {'username': views.USER,
                                                    'email': 'invalidemail'})

        self.assertTemplateUsed(response, 'register.html')
        self.assertContains(response, 'Must enter valid e-mail')

    def test_users_req(self):
        """Verify users request shows all registered users"""
        response = self.client.get('/users/')

        # Check that the response is 200 OK.
        self.failUnlessEqual(response.status_code, 200)

        # Note: There are 2 templates rendered, the context variable has
        #       a list for each one, and we want to check the first one

        # No users yet
        self.failUnlessEqual(len(response.context[0]['users']), 0)
        self.assertTemplateUsed(response, 'users.html')

        # Add users and verify there is one
        user = TwitterUser(username='testuser', email=TEST_EMAIL)
        user.save()

        response = self.client.get('/users/')
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(len(response.context[0]['users']), 1)
        self.assertTemplateUsed(response, 'users.html')

    def test_update_req_not_registered(self):
        """Update fails b/c user not registered locally"""

        user = 'durden20'
        response = self.client.get('/update/durden20')
        self.assertTemplateUsed(response, 'register.html')
        self.assertContains(response,
                            'Please register user (%s) first' % (user))


class ViewHelperTests(TestCase):
    """Class of tests for tweetapp views.py helper functions"""

    def test_get_api_success(self):
        """Successfully returns api reference with valid twitter cred."""

        api = views._get_api(views.USER, views.PASS)
        self.failIfEqual(api, None)

    def test_get_api_invalid_cred(self):
        """Unable to get api reference with invalid twitter cred."""

        self.failUnlessRaises(views.InvalidTwitterCred, views._get_api,
                                'bad123321', 'badpass')

    def test_lookup_twitter_user_success(self):
        """Successfully lookup twitter user"""

        user = views._lookup_twitter_user(views.USER)
        self.failIfEqual(user, None)
        self.failUnlessEqual(user['screen_name'], views.USER)

    def test_lookup_twitter_user_invalid_user(self):
        """Unable to find twitter user"""

        self.failUnlessRaises(views.InvalidTwitterCred,
                                views._lookup_twitter_user, 'bad123321')

    def test_local_user_add(self):
        """Add local user when not found"""

        # Check returned object
        ret_user = views._get_local_user(views.USER, TEST_EMAIL)
        self.failUnlessEqual(ret_user.username, views.USER)
        self.failUnlessEqual(ret_user.email, TEST_EMAIL)

        # Check DB
        db_user = TwitterUser.objects.all()[0]
        self.failUnlessEqual(db_user.username, ret_user.username)
        self.failUnlessEqual(db_user.email, ret_user.email)

    def test_local_user_add_invalid_twitter_user(self):
        """Unable to create local user with invalid twitter cred."""

        # Check returned object
        self.failUnlessRaises(views.InvalidTwitterCred,
                                views._get_local_user, 'bad123321',
                                TEST_EMAIL)

        # Check DB didn't add user
        self.failUnlessEqual(len(TwitterUser.objects.all()), 0)
