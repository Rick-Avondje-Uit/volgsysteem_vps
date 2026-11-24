from django.test import SimpleTestCase
from django.urls import resolve, reverse
from accounts.views.login import login_view




class AccountsUrlTests(SimpleTestCase):

    def test_login_url_reverse(self):
        self.assertEqual(reverse("login"), "/accounts/login/")

    def test_logout_url_reverse(self):
        self.assertEqual(reverse("logout"), "/accounts/logout/")

    def test_login_url_resolves_to_login_view(self):
        match = resolve("/accounts/login/")
        self.assertEqual(match.func, login_view)