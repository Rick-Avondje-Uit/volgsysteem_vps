from urllib.parse import parse_qs, urlparse

from django.test import SimpleTestCase, override_settings

from core.services.weeztix.exceptions import (
    WeeztixAuthenticationError,
)
from core.services.weeztix.oauth import build_authorization_url


@override_settings(
    WEEZTIX_AUTHORIZATION_URL=(
        "https://login.weeztix.com/authorize"
    ),
    WEEZTIX_CLIENT_ID="test-client-id",
)
class BuildAuthorizationUrlTests(SimpleTestCase):
    def test_builds_authorization_url(self):
        url = build_authorization_url(
            state="test-state",
            redirect_uri=(
                "https://example.com/weeztix/callback/"
            ),
        )

        parsed_url = urlparse(url)
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
            parsed_url.path,
            "/authorize",
        )
        self.assertEqual(
            parameters["response_type"],
            ["code"],
        )
        self.assertEqual(
            parameters["client_id"],
            ["test-client-id"],
        )
        self.assertEqual(
            parameters["redirect_uri"],
            [
                "https://example.com/weeztix/callback/",
            ],
        )
        self.assertEqual(
            parameters["state"],
            ["test-state"],
        )

    @override_settings(
        WEEZTIX_AUTHORIZATION_URL=(
            "https://login.weeztix.com/authorize"
            "?existing=value"
        )
    )
    def test_preserves_existing_query_parameters(self):
        url = build_authorization_url(
            state="test-state",
            redirect_uri=(
                "https://example.com/weeztix/callback/"
            ),
        )

        parameters = parse_qs(urlparse(url).query)

        self.assertEqual(
            parameters["existing"],
            ["value"],
        )
        self.assertEqual(
            parameters["state"],
            ["test-state"],
        )

    @override_settings(
        WEEZTIX_AUTHORIZATION_URL=None,
    )
    def test_raises_when_authorization_url_is_missing(self):
        with self.assertRaisesMessage(
            WeeztixAuthenticationError,
            "WEEZTIX_AUTHORIZATION_URL ontbreekt.",
        ):
            build_authorization_url(
                state="test-state",
                redirect_uri=(
                    "https://example.com/weeztix/callback/"
                ),
            )

    @override_settings(
        WEEZTIX_CLIENT_ID=None,
    )
    def test_raises_when_client_id_is_missing(self):
        with self.assertRaisesMessage(
            WeeztixAuthenticationError,
            "WEEZTIX_CLIENT_ID ontbreekt.",
        ):
            build_authorization_url(
                state="test-state",
                redirect_uri=(
                    "https://example.com/weeztix/callback/"
                ),
            )

    def test_raises_when_state_is_missing(self):
        with self.assertRaisesMessage(
            WeeztixAuthenticationError,
            "De OAuth state-waarde ontbreekt.",
        ):
            build_authorization_url(
                state="",
                redirect_uri=(
                    "https://example.com/weeztix/callback/"
                ),
            )

    def test_raises_when_redirect_uri_is_missing(self):
        with self.assertRaisesMessage(
            WeeztixAuthenticationError,
            "De Weeztix redirect_uri ontbreekt.",
        ):
            build_authorization_url(
                state="test-state",
                redirect_uri="",
            )