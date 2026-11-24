from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import Client

HERE = Path(__file__).parent


class BaseTest(TestCase):

    fixtures = [Path(HERE, "testdump.json")]
    username = "test_admin"
    email = "test_admin@example.com"
    password = "test_password"


    def setUp(self):
        super().setUp()

        User = get_user_model()

        self.user = User.objects.create_superuser(
            username=self.username,
            email=self.email,
            password=self.password,
        )

    def tearDown(self):
        self.logout()

    def login(self):
        self.client.force_login(self.user)
        return True

    def logout(self):
        """Log the user out."""
        self.client.logout()
