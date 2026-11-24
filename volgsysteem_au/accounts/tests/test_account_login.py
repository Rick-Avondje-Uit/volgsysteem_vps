from django.test import TestCase
from django.urls import reverse


class LoginViewTests(TestCase):

    def test_login_page_is_available(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)