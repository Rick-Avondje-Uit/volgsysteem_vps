from __future__ import annotations
from typing import Any
import requests
from django.conf import settings
from .exceptions import WeeztixConnectionError, WeeztixHTTPError, WeeztixResponseError
from .token_service import WeeztixTokenData, WeeztixTokenService


class WeeztixClient:
    BASE_URL = settings.WEEZTIX_API_BASE_URL

    DEFAULT_TIMEOUT = 30
    DOWNLOAD_TIMEOUT = 60

    def __init__(self, *, user, token_service=None, session=None) -> None:
        if user is None or not getattr(
            user,
            "is_authenticated",
            False,
        ):
            raise ValueError(
                "WeeztixClient vereist een ingelogde Django-gebruiker."
            )

        self.user = user
        self.session = session or requests.Session()
        self.token_service = (
            token_service
            or WeeztixTokenService(
                session=self.session,
            )
        )
        self._token: WeeztixTokenData | None = None

    @classmethod
    def from_user(cls, user, **kwargs) -> WeeztixClient:
        return cls(
            user=user,
            **kwargs,
        )

    @classmethod
    def _build_url(cls, url: str) -> str:
        """
        Bouw een volledige Weeztix-URL.

        Ondersteunt zowel relatieve API-paden:

            /event
            event/123/shops

        als reeds volledige URLs:

            https://api.weeztix.com/event

        Volledige URLs blijven ongewijzigd.
        """
        if not isinstance(url, str) or not url.strip():
            raise ValueError(
                "Een geldige Weeztix-URL of API-pad is vereist."
            )

        url = url.strip()

        if url.startswith(
            (
                "http://",
                "https://",
            )
        ):
            return url

        return (
            f"{cls.BASE_URL.rstrip('/')}/"
            f"{url.lstrip('/')}"
        )

    def _get_token(self, *, force_refresh=False) -> WeeztixTokenData:
        if self._token is None or force_refresh:
            self._token = self.token_service.get_for_user(
                self.user,
                force_refresh=force_refresh,
            )

        return self._token

    def _headers(self, accept="application/json",) -> dict[str, str]:
        token = self._get_token()

        headers = {
            "Authorization": (
                f"{token.token_type} "
                f"{token.access_token}"
            ),
            "Accept": accept,
        }

        company = getattr(
            settings,
            "WEEZTIX_COMPANY_ID",
            None,
        )

        if company:
            headers["Company"] = str(company)

        return headers

    def _request(
        self, method, url, *, params=None, json=None, data=None, timeout=None, accept="application/json", retry=True):
        url = self._build_url(url)

        try:
            response = self.session.request(
                method,
                url,
                headers=self._headers(accept),
                params=params,
                json=json,
                data=data,
                timeout=(
                    timeout
                    or self.DEFAULT_TIMEOUT
                ),
            )

        except requests.RequestException as exc:
            raise WeeztixConnectionError(
                f"Verbinding met Weeztix mislukt: {exc}"
            ) from exc

        if response.status_code == 401 and retry:
            self._token = None

            self._get_token(
                force_refresh=True,
            )

            return self._request(
                method,
                url,
                params=params,
                json=json,
                data=data,
                timeout=timeout,
                accept=accept,
                retry=False,
            )

        if not response.ok:
            raise WeeztixHTTPError(
                f"Weeztix {method} {url} mislukt: "
                f"HTTP {response.status_code} "
                f"{response.text}"
            )

        return response

    @staticmethod
    def _json(response) -> Any:
        if not response.content:
            return None

        try:
            return response.json()

        except ValueError as exc:
            raise WeeztixResponseError(
                "Weeztix gaf geen geldige JSON-response."
            ) from exc

    def get(self, url, *, params=None) -> Any:
        return self._json(
            self._request(
                "GET",
                url,
                params=params,
            )
        )

    def post(
        self,url, *, json=None, data=None) -> Any:
        return self._json(
            self._request(
                "POST",
                url,
                json=json,
                data=data,
            )
        )

    def delete(self, url) -> Any:
        return self._json(
            self._request(
                "DELETE",
                url,
            )
        )

    def download(self, url) -> bytes:
        response = self._request(
            "GET",
            url,
            timeout=self.DOWNLOAD_TIMEOUT,
            accept=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet,"
                "application/octet-stream"
            ),
        )

        if not response.content:
            raise WeeztixResponseError(
                "Weeztix gaf een leeg bestand terug."
            )

        return response.content