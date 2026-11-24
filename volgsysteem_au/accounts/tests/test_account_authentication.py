from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AuthenticationTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="testgebruiker",
            email="test@example.com",
            password="TestWachtwoord123!",
        )

    def test_user_can_login(self):
        logged_in = self.client.login(
            username="testgebruiker",
            password="TestWachtwoord123!",
        )

        self.assertTrue(logged_in)

    def test_user_can_logout(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("logout"))

        self.assertFalse("_auth_user_id" in self.client.session)