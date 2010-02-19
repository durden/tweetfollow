"""Tests for tweetapp application"""

import unittest
from django.test.client import Client
from models import TwitterUser

class TweetappTests(unittest.TestCase):
    """Class of tests for tweetapp"""

    def __add_user(self, username, email):
        """Add a user to local DB"""
        user = TwitterUser(username=username, email=email)
        user.save()

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
        email = 'luke@lukelee.net'

        response = self.client.post('/register/',
                                    {'user': name, 'email': email})

        # Check that the response is 200 OK.
        self.failUnlessEqual(response.status_code, 200)

        # Should go to home
        self.failUnlessEqual(response.template[0].name, 'home.html')

        # Verify user in local DB
        users = TwitterUser.objects.all()
        self.failUnlessEqual(len(users), 1)
        self.failUnlessEqual(users[0].email, email)
        self.failUnlessEqual(users[0].username, name)

    def test_users_req(self):
        """Verify users request shows all registered users"""
        response = self.client.get('/users/')

        # Check that the response is 200 OK.
        self.failUnlessEqual(response.status_code, 200)

        # Note: There are 2 templates rendered, the context variable has
        #       a list for each one, and we want to check the first one

        # No users yet
        self.failUnlessEqual(len(response.context[0]['users']), 0)

        # Add users and verify there is one
        self.__add_user('testuser', 'fake_email')

        response = self.client.get('/users/')
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(len(response.context[0]['users']), 1)
