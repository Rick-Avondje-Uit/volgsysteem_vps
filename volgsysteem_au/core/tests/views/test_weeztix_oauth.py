import http
from datetime import timedelta
from unittest.mock import patch
from urllib import request
from urllib.parse import parse_qs, urlparse
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from core.services.weeztix.exceptions import WeeztixAuthenticationError
from core.services.weeztix.token_service import WeeztixTokenData
from core.views import weeztix
from core.views.weeztix import WEEZTIX_OAUTH_STATE_SESSION_KEY


FERNET_KEY = Fernet.generate_key().decode()


@override_settings(
    WEEZTIX_AUTHORIZATION_URL=(
        "https://login.weeztix.com/authorize"
    ),
    WEEZTIX_CLIENT_ID="test-client-id",
    WEEZTIX_CLIENT_SECRET="test-client-secret",
    WEEZTIX_TOKEN_URL="https://auth.weeztix.com/tokens",
    WEEZTIX_TOKEN_ENCRYPTION_KEY=FERNET_KEY,
)
class WeeztixOAuthViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()

        self.user = user_model.objects.create_user(
            username="oauth-view-user",
            email="oauth-view@example.com",
            password="test-password",
        )

        self.redirect_url = reverse(
            "core:weeztix_redirect"
        )
        self.callback_url = reverse(
            "core:weeztix_callback"
        )

        self.client.force_login(self.user)

    @staticmethod
    def messages_from_response(response):
        return [
            str(message)
            for message in get_messages(response.wsgi_request)
        ]

    def store_state(self, state="expected-state"):
        session = self.client.session
        session[WEEZTIX_OAUTH_STATE_SESSION_KEY] = state
        session.save()

    def test_redirect_requires_login(self):
        self.client.logout()

        response = self.client.get(
            self.redirect_url,
        )

        self.assertEqual(
            response.status_code,
            302,
        )
        self.assertIn(
            "/login/",
            response.url,
        )

    @override_settings(WEEZTIX_REDIRECT_URI="http://127.0.0.1:8000/weeztix/callback/")
    def test_redirect_stores_state_and_redirects_to_weeztix(self,):
        response = self.client.get(reverse("core:weeztix_redirect"))

        self.assertEqual(
            response.status_code,
            302,
        )

        parsed_url = urlparse(response.url)
        parameters = parse_qs(parsed_url.query)

        self.assertEqual(
            parsed_url.scheme,
            "https",
        )
        self.assertEqual(
            parsed_url.netloc,
            "login.weeztix.com",
        )
        self.assertEqual(
            parameters["response_type"],
            ["code"],
        )
        self.assertEqual(
            parameters["client_id"],
            ["test-client-id"],
        )

        session_state = self.client.session[
            WEEZTIX_OAUTH_STATE_SESSION_KEY
        ]

        self.assertEqual(
            parameters["state"],
            [session_state],
        )

        expected_callback = settings.WEEZTIX_REDIRECT_URI

        self.assertEqual(
            parameters["redirect_uri"],
            [expected_callback]
        )

    def test_callback_requires_login(self):
        self.client.logout()

        response = self.client.get(
            self.callback_url,
            {
                "code": "authorization-code",
                "state": "expected-state",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )
        self.assertIn(
            "/login/",
            response.url,
        )

    def test_callback_handles_oauth_error(self):
        self.store_state()

        response = self.client.get(
            self.callback_url,
            {
                "error": "access_denied",
                "error_description": (
                    "De gebruiker heeft toegang geweigerd"
                ),
            },
            follow=True,
        )

        messages = self.messages_from_response(response)

        self.assertTrue(
            any(
                "De Weeztix-koppeling is niet voltooid"
                in message
                for message in messages
            )
        )
        self.assertNotIn(
            WEEZTIX_OAUTH_STATE_SESSION_KEY,
            self.client.session,
        )

    def test_callback_rejects_missing_session_state(self):
        response = self.client.get(
            self.callback_url,
            {
                "code": "authorization-code",
                "state": "received-state",
            },
            follow=True,
        )

        messages = self.messages_from_response(response)

        self.assertTrue(
            any(
                "OAuth-sessie ontbreekt of is verlopen"
                in message
                for message in messages
            )
        )

    def test_callback_rejects_invalid_state(self):
        self.store_state(
            "expected-state",
        )

        response = self.client.get(
            self.callback_url,
            {
                "code": "authorization-code",
                "state": "wrong-state",
            },
            follow=True,
        )

        messages = self.messages_from_response(response)

        self.assertTrue(
            any(
                "state-waarde is ongeldig"
                in message
                for message in messages
            )
        )
        self.assertNotIn(
            WEEZTIX_OAUTH_STATE_SESSION_KEY,
            self.client.session,
        )

    def test_callback_rejects_missing_code(self):
        self.store_state(
            "expected-state",
        )

        response = self.client.get(
            self.callback_url,
            {
                "state": "expected-state",
            },
            follow=True,
        )

        messages = self.messages_from_response(response)

        self.assertTrue(
            any(
                "geen authorization code"
                in message
                for message in messages
            )
        )

    @patch(
        "core.views.weeztix.WeeztixTokenService"
    )
    def test_callback_exchanges_code_and_saves_token(
        self,
        token_service_class,
    ):
        self.store_state(
            "expected-state",
        )

        token = WeeztixTokenData(
            access_token="access-token",
            refresh_token="refresh-token",
            token_type="Bearer",
            expires_at=(
                timezone.now() + timedelta(days=3)
            ),
            refresh_token_expires_at=(
                timezone.now() + timedelta(days=365)
            ),
        )

        token_service = token_service_class.return_value
        token_service.exchange_authorization_code.return_value = (
            token
        )

        response = self.client.get(
            self.callback_url,
            {
                "code": "authorization-code",
                "state": "expected-state",
            },
            follow=True,
        )

        expected_redirect_uri = (
            "http://testserver"
            f"{self.callback_url}"
        )

        token_service.exchange_authorization_code.assert_called_once_with(
            code="authorization-code",
            redirect_uri=expected_redirect_uri,
        )
        token_service.save_for_user.assert_called_once_with(
            user=self.user,
            token=token,
            scope="",
        )

        messages = self.messages_from_response(response)

        self.assertTrue(
            any(
                "succesvol opgeslagen"
                in message
                for message in messages
            )
        )

    @patch(
        "core.views.weeztix.WeeztixTokenService"
    )
    def test_callback_handles_token_service_error(
        self,
        token_service_class,
    ):
        self.store_state(
            "expected-state",
        )

        token_service = token_service_class.return_value
        token_service.exchange_authorization_code.side_effect = (
            WeeztixAuthenticationError(
                "Tokenaanvraag mislukt."
            )
        )

        response = self.client.get(
            self.callback_url,
            {
                "code": "authorization-code",
                "state": "expected-state",
            },
            follow=True,
        )

        token_service.save_for_user.assert_not_called()

        messages = self.messages_from_response(response)

        self.assertTrue(
            any(
                "Tokenaanvraag mislukt"
                in message
                for message in messages
            )
        )