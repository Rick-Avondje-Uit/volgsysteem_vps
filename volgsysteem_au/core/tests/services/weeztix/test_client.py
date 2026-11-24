from datetime import timedelta
from unittest.mock import Mock
import requests
from django.test import SimpleTestCase, override_settings
from django.utils import timezone
from core.services.weeztix.client import WeeztixClient
from core.services.weeztix.exceptions import WeeztixConnectionError, WeeztixHTTPError, WeeztixResponseError
from core.services.weeztix.token_service import WeeztixTokenData


class WeeztixClientTests(SimpleTestCase):
    def setUp(self):
        self.user = Mock()
        self.user.is_authenticated = True

        self.session = Mock()
        self.token_service = Mock()

        self.token = WeeztixTokenData(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            token_type="Bearer",
            expires_at=timezone.now() + timedelta(hours=1),
            refresh_token_expires_at=(
                timezone.now() + timedelta(days=30)
            ),
        )

        self.token_service.get_for_user.return_value = self.token

        self.client = WeeztixClient(
            user=self.user,
            token_service=self.token_service,
            session=self.session,
        )

    @staticmethod
    def make_response(
        *,
        status_code=200,
        json_data=None,
        content=b"response",
        text="",
    ):
        response = Mock()

        response.status_code = status_code
        response.ok = 200 <= status_code < 300
        response.content = content
        response.text = text
        response.json.return_value = json_data

        return response

    def test_requires_authenticated_user(self):
        anonymous_user = Mock()
        anonymous_user.is_authenticated = False

        with self.assertRaisesMessage(
            ValueError,
            "WeeztixClient vereist een ingelogde Django-gebruiker.",
        ):
            WeeztixClient(
                user=anonymous_user,
            )

    def test_requires_user(self):
        with self.assertRaisesMessage(
            ValueError,
            "WeeztixClient vereist een ingelogde Django-gebruiker.",
        ):
            WeeztixClient(
                user=None,
            )

    def test_from_user_creates_client(self):
        client = WeeztixClient.from_user(
            self.user,
            token_service=self.token_service,
            session=self.session,
        )

        self.assertIs(
            client.user,
            self.user,
        )
        self.assertIs(
            client.token_service,
            self.token_service,
        )
        self.assertIs(
            client.session,
            self.session,
        )

    def test_get_token_uses_token_service(self):
        token = self.client._get_token()

        self.assertIs(
            token,
            self.token,
        )

        self.token_service.get_for_user.assert_called_once_with(
            self.user,
            force_refresh=False,
        )

    def test_get_token_is_cached(self):
        first = self.client._get_token()
        second = self.client._get_token()

        self.assertIs(
            first,
            second,
        )

        self.token_service.get_for_user.assert_called_once_with(
            self.user,
            force_refresh=False,
        )

    def test_force_refresh_requests_new_token(self):
        refreshed_token = WeeztixTokenData(
            access_token="refreshed-access-token",
            refresh_token="refreshed-refresh-token",
            token_type="Bearer",
            expires_at=timezone.now() + timedelta(hours=1),
            refresh_token_expires_at=(
                timezone.now() + timedelta(days=30)
            ),
        )

        self.token_service.get_for_user.side_effect = [
            self.token,
            refreshed_token,
        ]

        first = self.client._get_token()

        refreshed = self.client._get_token(
            force_refresh=True,
        )

        self.assertIs(
            first,
            self.token,
        )
        self.assertIs(
            refreshed,
            refreshed_token,
        )

        self.assertEqual(
            self.token_service.get_for_user.call_count,
            2,
        )

        self.token_service.get_for_user.assert_any_call(
            self.user,
            force_refresh=True,
        )

    def test_headers_contains_authorization_header(self):
        headers = self.client._headers()

        self.assertEqual(
            headers["Authorization"],
            "Bearer test-access-token",
        )

        self.assertEqual(
            headers["Accept"],
            "application/json",
        )

    @override_settings(
        WEEZTIX_COMPANY_ID="company-guid",
    )
    def test_headers_contains_company_header(self):
        headers = self.client._headers()

        self.assertEqual(
            headers["Company"],
            "company-guid",
        )

    @override_settings(
        WEEZTIX_COMPANY_ID=None,
    )
    def test_headers_omits_company_when_not_configured(self):
        headers = self.client._headers()

        self.assertNotIn(
            "Company",
            headers,
        )

    def test_get_returns_parsed_json(self):
        response = self.make_response(
            json_data={
                "guid": "event-guid",
                "name": "Test event",
            },
        )

        self.session.request.return_value = response

        result = self.client.get(
            "https://api.example.test/events/event-guid",
        )

        self.assertEqual(
            result,
            {
                "guid": "event-guid",
                "name": "Test event",
            },
        )

        self.session.request.assert_called_once_with(
            "GET",
            "https://api.example.test/events/event-guid",
            headers={
                "Authorization": "Bearer test-access-token",
                "Accept": "application/json",
            },
            params=None,
            json=None,
            data=None,
            timeout=30,
        )

    def test_get_sends_query_parameters(self):
        response = self.make_response(
            json_data={
                "data": [],
            },
        )

        self.session.request.return_value = response

        result = self.client.get(
            "https://api.example.test/events",
            params={
                "page": 2,
            },
        )

        self.assertEqual(
            result,
            {
                "data": [],
            },
        )

        self.session.request.assert_called_once_with(
            "GET",
            "https://api.example.test/events",
            headers={
                "Authorization": "Bearer test-access-token",
                "Accept": "application/json",
            },
            params={
                "page": 2,
            },
            json=None,
            data=None,
            timeout=30,
        )

    def test_post_sends_json_payload(self):
        response = self.make_response(
            status_code=201,
            json_data={
                "guid": "export-guid",
            },
        )

        self.session.request.return_value = response

        result = self.client.post(
            "https://api.example.test/export",
            json={
                "type": "orders_and_order_tickets",
            },
        )

        self.assertEqual(
            result,
            {
                "guid": "export-guid",
            },
        )

        self.session.request.assert_called_once_with(
            "POST",
            "https://api.example.test/export",
            headers={
                "Authorization": "Bearer test-access-token",
                "Accept": "application/json",
            },
            params=None,
            json={
                "type": "orders_and_order_tickets",
            },
            data=None,
            timeout=30,
        )

    def test_post_can_send_form_data(self):
        response = self.make_response(
            json_data={
                "success": True,
            },
        )

        self.session.request.return_value = response

        result = self.client.post(
            "https://api.example.test/test",
            data={
                "value": "test",
            },
        )

        self.assertEqual(
            result,
            {
                "success": True,
            },
        )

        self.session.request.assert_called_once_with(
            "POST",
            "https://api.example.test/test",
            headers={
                "Authorization": "Bearer test-access-token",
                "Accept": "application/json",
            },
            params=None,
            json=None,
            data={
                "value": "test",
            },
            timeout=30,
        )

    def test_delete_returns_parsed_json(self):
        response = self.make_response(
            json_data={
                "deleted": True,
            },
        )

        self.session.request.return_value = response

        result = self.client.delete(
            "https://api.example.test/export/export-guid",
        )

        self.assertEqual(
            result,
            {
                "deleted": True,
            },
        )

    def test_delete_accepts_empty_response(self):
        response = self.make_response(
            status_code=204,
            content=b"",
            json_data=None,
        )

        self.session.request.return_value = response

        result = self.client.delete(
            "https://api.example.test/export/export-guid",
        )

        self.assertIsNone(result)

        response.json.assert_not_called()

    def test_connection_error_is_translated(self):
        self.session.request.side_effect = (
            requests.ConnectionError(
                "Connection failed",
            )
        )

        with self.assertRaises(
            WeeztixConnectionError,
        ):
            self.client.get(
                "https://api.example.test/events",
            )

    def test_timeout_is_translated(self):
        self.session.request.side_effect = (
            requests.Timeout(
                "Request timed out",
            )
        )

        with self.assertRaises(
            WeeztixConnectionError,
        ):
            self.client.get(
                "https://api.example.test/events",
            )

    def test_http_error_is_translated(self):
        response = self.make_response(
            status_code=500,
            text="Internal Server Error",
        )

        self.session.request.return_value = response

        with self.assertRaisesMessage(
            WeeztixHTTPError,
            "HTTP 500",
        ):
            self.client.get(
                "https://api.example.test/events",
            )

    def test_invalid_json_raises_response_error(self):
        response = self.make_response(
            json_data=None,
        )

        response.json.side_effect = ValueError(
            "Invalid JSON",
        )

        self.session.request.return_value = response

        with self.assertRaisesMessage(
            WeeztixResponseError,
            "Weeztix gaf geen geldige JSON-response.",
        ):
            self.client.get(
                "https://api.example.test/events",
            )

    def test_401_refreshes_token_and_retries_once(self):
        unauthorized = self.make_response(
            status_code=401,
            text="Unauthorized",
        )

        success = self.make_response(
            status_code=200,
            json_data={
                "guid": "event-guid",
            },
        )

        refreshed_token = WeeztixTokenData(
            access_token="refreshed-access-token",
            refresh_token="rotated-refresh-token",
            token_type="Bearer",
            expires_at=timezone.now() + timedelta(hours=1),
            refresh_token_expires_at=(
                timezone.now() + timedelta(days=30)
            ),
        )

        self.session.request.side_effect = [
            unauthorized,
            success,
        ]

        self.token_service.get_for_user.side_effect = [
            self.token,
            refreshed_token,
        ]

        result = self.client.get(
            "https://api.example.test/events/event-guid",
        )

        self.assertEqual(
            result,
            {
                "guid": "event-guid",
            },
        )

        self.assertEqual(
            self.session.request.call_count,
            2,
        )

        self.token_service.get_for_user.assert_any_call(
            self.user,
            force_refresh=True,
        )

        second_request = self.session.request.call_args_list[1]

        self.assertEqual(
            second_request.kwargs["headers"]["Authorization"],
            "Bearer refreshed-access-token",
        )

    def test_second_401_is_not_retried(self):
        first_response = self.make_response