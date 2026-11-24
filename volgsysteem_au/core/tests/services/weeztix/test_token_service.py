from datetime import timedelta
from unittest.mock import Mock
from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from core.models.weeztix_oauth import WeeztixOAuthToken
from core.services.weeztix.exceptions import WeeztixAuthenticationError, WeeztixConnectionError, WeeztixResponseError
from core.services.weeztix.token_crypto import decrypt_token, encrypt_token
from core.services.weeztix.token_service import WeeztixTokenData, WeeztixTokenService


FERNET_KEY = Fernet.generate_key().decode()


@override_settings(
    WEEZTIX_CLIENT_ID="test-client-id",
    WEEZTIX_CLIENT_SECRET="test-client-secret",
    WEEZTIX_TOKEN_URL="https://auth.weeztix.com/tokens",
    WEEZTIX_TOKEN_ENCRYPTION_KEY=FERNET_KEY,
)
class WeeztixTokenServiceTests(TestCase):
    def setUp(self):
        user_model = get_user_model()

        self.user = user_model.objects.create_user(
            username="oauth-test-user",
            email="oauth@example.com",
            password="test-password",
        )

        self.session = Mock()
        self.service = WeeztixTokenService(
            session=self.session,
        )

    def make_response(
        self,
        *,
        status_code=200,
        json_data=None,
        text="",
    ):
        response = Mock()
        response.status_code = status_code
        response.ok = 200 <= status_code < 300
        response.text = text
        response.json.return_value = json_data
        return response

    def create_stored_token(
        self,
        *,
        access_token="stored-access-token",
        refresh_token="stored-refresh-token",
        expires_at=None,
        refresh_token_expires_at=None,
    ):
        if expires_at is None:
            expires_at = timezone.now() + timedelta(hours=1)

        if refresh_token_expires_at is None:
            refresh_token_expires_at = (
                timezone.now() + timedelta(days=30)
            )

        return WeeztixOAuthToken.objects.create(
            user=self.user,
            encrypted_access_token=encrypt_token(
                access_token
            ),
            encrypted_refresh_token=encrypt_token(
                refresh_token
            ),
            token_type="Bearer",
            expires_at=expires_at,
            refresh_token_expires_at=(
                refresh_token_expires_at
            ),
        )

    def test_oauth_settings_returns_configured_values(self):
        result = self.service._oauth_settings()

        self.assertEqual(
            result,
            (
                "test-client-id",
                "test-client-secret",
                "https://auth.weeztix.com/tokens",
            ),
        )

    @override_settings(
        WEEZTIX_CLIENT_ID=None,
    )
    def test_oauth_settings_rejects_incomplete_settings(self):
        with self.assertRaisesMessage(
            WeeztixAuthenticationError,
            "Weeztix OAuth-instellingen zijn onvolledig.",
        ):
            self.service._oauth_settings()

    def test_exchange_authorization_code(self):
        self.session.post.return_value = self.make_response(
            json_data={
                "access_token": "new-access-token",
                "refresh_token": "new-refresh-token",
                "token_type": "Bearer",
                "expires_in": 259200,
                "refresh_token_expires_in": 31535999,
            },
        )

        token = self.service.exchange_authorization_code(
            code="authorization-code",
            redirect_uri=(
                "https://example.com/weeztix/callback/"
            ),
        )

        self.assertEqual(
            token.access_token,
            "new-access-token",
        )
        self.assertEqual(
            token.refresh_token,
            "new-refresh-token",
        )
        self.assertEqual(
            token.token_type,
            "Bearer",
        )

        self.session.post.assert_called_once_with(
            "https://auth.weeztix.com/tokens",
            json={
                "grant_type": "authorization_code",
                "code": "authorization-code",
                "client_id": "test-client-id",
                "client_secret": "test-client-secret",
                "redirect_uri": (
                    "https://example.com/weeztix/callback/"
                ),
            },
            headers={
                "Accept": "application/json",
            },
            timeout=30,
        )

    def test_exchange_authorization_code_requires_code(self):
        with self.assertRaisesMessage(
            WeeztixAuthenticationError,
            "De Weeztix authorization code ontbreekt.",
        ):
            self.service.exchange_authorization_code(
                code="",
                redirect_uri=(
                    "https://example.com/weeztix/callback/"
                ),
            )

        self.session.post.assert_not_called()

    def test_exchange_authorization_code_requires_redirect_uri(
        self,
    ):
        with self.assertRaisesMessage(
            WeeztixAuthenticationError,
            "De Weeztix redirect URI ontbreekt.",
        ):
            self.service.exchange_authorization_code(
                code="authorization-code",
                redirect_uri="",
            )

        self.session.post.assert_not_called()

    def test_exchange_requires_refresh_token_in_response(self):
        self.session.post.return_value = self.make_response(
            json_data={
                "access_token": "new-access-token",
                "token_type": "Bearer",
                "expires_in": 259200,
            },
        )

        with self.assertRaisesMessage(
            WeeztixResponseError,
            "Weeztix heeft geen refresh-token teruggegeven.",
        ):
            self.service.exchange_authorization_code(
                code="authorization-code",
                redirect_uri=(
                    "https://example.com/weeztix/callback/"
                ),
            )

    def test_refreshes_access_token(self):
        self.session.post.return_value = self.make_response(
            json_data={
                "access_token": "refreshed-access-token",
                "refresh_token": "rotated-refresh-token",
                "token_type": "Bearer",
                "expires_in": 259200,
                "refresh_token_expires_in": 31535999,
            },
        )

        token = self.service.refresh(
            "old-refresh-token",
        )

        self.assertEqual(
            token.access_token,
            "refreshed-access-token",
        )
        self.assertEqual(
            token.refresh_token,
            "rotated-refresh-token",
        )

        self.session.post.assert_called_once_with(
            "https://auth.weeztix.com/tokens",
            json={
                "grant_type": "refresh_token",
                "refresh_token": "old-refresh-token",
                "client_id": "test-client-id",
                "client_secret": "test-client-secret",
            },
            headers={
                "Accept": "application/json",
            },
            timeout=30,
        )

    def test_refresh_requires_refresh_token(self):
        with self.assertRaisesMessage(
            WeeztixAuthenticationError,
            "Het Weeztix-refresh-token ontbreekt.",
        ):
            self.service.refresh("")

        self.session.post.assert_not_called()

    def test_refresh_requires_new_rotated_refresh_token(self):
        self.session.post.return_value = self.make_response(
            json_data={
                "access_token": "refreshed-access-token",
                "token_type": "Bearer",
                "expires_in": 259200,
            },
        )

        with self.assertRaisesMessage(
            WeeztixResponseError,
            "Token-refresh gaf geen nieuw refresh-token.",
        ):
            self.service.refresh(
                "old-refresh-token",
            )

    def test_get_for_user_returns_valid_stored_token(self):
        self.create_stored_token()

        token = self.service.get_for_user(
            self.user,
        )

        self.assertEqual(
            token.access_token,
            "stored-access-token",
        )
        self.assertEqual(
            token.refresh_token,
            "stored-refresh-token",
        )
        self.session.post.assert_not_called()

    def test_get_for_user_refreshes_expired_token(self):
        stored_token = self.create_stored_token(
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        self.session.post.return_value = self.make_response(
            json_data={
                "access_token": "refreshed-access-token",
                "refresh_token": "rotated-refresh-token",
                "token_type": "Bearer",
                "expires_in": 259200,
                "refresh_token_expires_in": 31535999,
            },
        )

        token = self.service.get_for_user(
            self.user,
        )

        self.assertEqual(
            token.access_token,
            "refreshed-access-token",
        )
        self.assertEqual(
            token.refresh_token,
            "rotated-refresh-token",
        )

        stored_token.refresh_from_db()

        self.assertEqual(
            decrypt_token(
                stored_token.encrypted_access_token
            ),
            "refreshed-access-token",
        )
        self.assertEqual(
            decrypt_token(
                stored_token.encrypted_refresh_token
            ),
            "rotated-refresh-token",
        )

    def test_get_for_user_force_refreshes_valid_token(self):
        self.create_stored_token(
            expires_at=timezone.now() + timedelta(hours=1),
        )

        self.session.post.return_value = self.make_response(
            json_data={
                "access_token": "forced-access-token",
                "refresh_token": "forced-refresh-token",
                "token_type": "Bearer",
                "expires_in": 259200,
                "refresh_token_expires_in": 31535999,
            },
        )

        token = self.service.get_for_user(
            self.user,
            force_refresh=True,
        )

        self.assertEqual(
            token.access_token,
            "forced-access-token",
        )
        self.session.post.assert_called_once()

    def test_get_for_user_rejects_expired_refresh_token(self):
        self.create_stored_token(
            expires_at=timezone.now() - timedelta(minutes=1),
            refresh_token_expires_at=(
                timezone.now() - timedelta(minutes=1)
            ),
        )

        with self.assertRaisesMessage(
            WeeztixAuthenticationError,
            "nieuwe autorisatie vereist",
        ):
            self.service.get_for_user(
                self.user,
            )

        self.session.post.assert_not_called()

    def test_get_for_user_rejects_anonymous_user(self):
        anonymous_user = Mock()
        anonymous_user.is_authenticated = False

        with self.assertRaisesMessage(
            WeeztixAuthenticationError,
            "Er is geen ingelogde gebruiker beschikbaar.",
        ):
            self.service.get_for_user(
                anonymous_user,
            )

    def test_get_for_user_rejects_missing_stored_token(self):
        with self.assertRaisesMessage(
            WeeztixAuthenticationError,
            "Voor deze gebruiker is geen Weeztix-token",
        ):
            self.service.get_for_user(
                self.user,
            )

    def test_save_for_user_encrypts_tokens(self):
        now = timezone.now()

        token = WeeztixTokenData(
            access_token="plain-access-token",
            refresh_token="plain-refresh-token",
            token_type="Bearer",
            expires_at=now + timedelta(days=3),
            refresh_token_expires_at=(
                now + timedelta(days=365)
            ),
        )

        oauth_token = self.service.save_for_user(
            user=self.user,
            token=token,
            scope="",
        )

        self.assertNotEqual(
            oauth_token.encrypted_access_token,
            "plain-access-token",
        )
        self.assertNotEqual(
            oauth_token.encrypted_refresh_token,
            "plain-refresh-token",
        )
        self.assertEqual(
            decrypt_token(
                oauth_token.encrypted_access_token
            ),
            "plain-access-token",
        )
        self.assertEqual(
            decrypt_token(
                oauth_token.encrypted_refresh_token
            ),
            "plain-refresh-token",
        )

    def test_save_for_user_updates_existing_record(self):
        existing = self.create_stored_token()

        token = WeeztixTokenData(
            access_token="updated-access-token",
            refresh_token="updated-refresh-token",
            token_type="Bearer",
            expires_at=timezone.now() + timedelta(days=3),
            refresh_token_expires_at=(
                timezone.now() + timedelta(days=365)
            ),
        )

        updated = self.service.save_for_user(
            user=self.user,
            token=token,
        )

        self.assertEqual(
            updated.pk,
            existing.pk,
        )
        self.assertEqual(
            WeeztixOAuthToken.objects.filter(
                user=self.user
            ).count(),
            1,
        )
        self.assertEqual(
            decrypt_token(
                updated.encrypted_access_token
            ),
            "updated-access-token",
        )

    def test_http_error_becomes_authentication_error(self):
        self.session.post.return_value = self.make_response(
            status_code=401,
            text="invalid_client",
        )

        with self.assertRaisesMessage(
            WeeztixAuthenticationError,
            "HTTP 401",
        ):
            self.service.exchange_authorization_code(
                code="authorization-code",
                redirect_uri=(
                    "https://example.com/weeztix/callback/"
                ),
            )

    def test_invalid_json_becomes_response_error(self):
        response = self.make_response(
            json_data=None,
        )
        response.json.side_effect = ValueError(
            "Invalid JSON"
        )
        self.session.post.return_value = response

        with self.assertRaises(
            WeeztixResponseError,
        ):
            self.service.exchange_authorization_code(
                code="authorization-code",
                redirect_uri=(
                    "https://example.com/weeztix/callback/"
                ),
            )

    def test_invalid_token_response_is_rejected(self):
        self.session.post.return_value = self.make_response(
            json_data={
                "refresh_token": "refresh-token",
            },
        )

        with self.assertRaisesMessage(
            WeeztixResponseError,
            "Ongeldige Weeztix-tokenresponse.",
        ):
            self.service.exchange_authorization_code(
                code="authorization-code",
                redirect_uri=(
                    "https://example.com/weeztix/callback/"
                ),
            )

    def test_connection_error_is_converted(self):
        import requests

        self.session.post.side_effect = (
            requests.ConnectionError(
                "Connection failed"
            )
        )

        with self.assertRaises(
            WeeztixConnectionError,
        ):
            self.service.exchange_authorization_code(
                code="authorization-code",
                redirect_uri=(
                    "https://example.com/weeztix/callback/"
                ),
            )