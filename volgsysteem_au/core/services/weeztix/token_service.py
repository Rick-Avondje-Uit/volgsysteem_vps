from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
import requests
from django.conf import settings
from django.db import transaction
from core.models.weeztix_oauth import WeeztixOAuthToken
from .exceptions import WeeztixAuthenticationError, WeeztixConnectionError, WeeztixResponseError
from .token_crypto import decrypt_token, encrypt_token

TOKEN_REFRESH_MARGIN = timedelta(minutes=5)
DEFAULT_TOKEN_URL = settings.WEEZTIX_TOKEN_URL

@dataclass(frozen=True)
class WeeztixTokenData:
    access_token: str
    refresh_token: str | None
    token_type: str
    expires_at: datetime
    refresh_token_expires_at: datetime | None = None

    def is_expired(self, margin: timedelta = TOKEN_REFRESH_MARGIN) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at - margin

    def refresh_token_is_expired(self) -> bool:
        return bool(self.refresh_token_expires_at and datetime.now(timezone.utc) >= self.refresh_token_expires_at)

class WeeztixTokenService:
    def __init__(self, *, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()

    def _oauth_settings(self) -> tuple[str, str, str]:
        client_id = getattr(settings, "WEEZTIX_CLIENT_ID", None)
        client_secret = getattr(settings, "WEEZTIX_CLIENT_SECRET", None)
        token_url = getattr(settings, "WEEZTIX_TOKEN_URL", DEFAULT_TOKEN_URL)

        if not client_id or not client_secret or not token_url:
            raise WeeztixAuthenticationError("Weeztix OAuth-instellingen zijn onvolledig.")

        return str(client_id), str(client_secret), str(token_url)

    def get_for_user(self, user, *, force_refresh: bool = False) -> WeeztixTokenData:
        if user is None or not getattr(user, "is_authenticated", False):
            raise WeeztixAuthenticationError("Er is geen ingelogde gebruiker beschikbaar.")

        try:
            oauth_token = WeeztixOAuthToken.objects.get(user=user)
        except WeeztixOAuthToken.DoesNotExist as exc:
            raise WeeztixAuthenticationError("Voor deze gebruiker is geen Weeztix-token opgeslagen.") from exc

        token = self.load_token(oauth_token)

        if not force_refresh and not token.is_expired():
            return token

        return self._refresh_for_user(
            user=user,
            force_refresh=force_refresh,
        )

    @transaction.atomic
    def _refresh_for_user(self, *, user, force_refresh: bool) -> WeeztixTokenData:
        try:
            oauth_token = (WeeztixOAuthToken.objects.select_for_update().get(user=user))
        except WeeztixOAuthToken.DoesNotExist as exc:
            raise WeeztixAuthenticationError(
                "Voor deze gebruiker is geen Weeztix-token opgeslagen."
            ) from exc

        token = self.load_token(oauth_token)

        if not force_refresh and not token.is_expired():
            return token

        if not token.refresh_token or token.refresh_token_is_expired():
            raise WeeztixAuthenticationError(
                "Weeztix-token kan niet worden vernieuwd; "
                "nieuwe autorisatie vereist."
            )

        refreshed = self.refresh(token.refresh_token)
        self.save_token(oauth_token, refreshed)
        return refreshed

    @staticmethod
    def load_token(oauth_token: WeeztixOAuthToken) -> WeeztixTokenData:
        access = decrypt_token(oauth_token.encrypted_access_token)
        refresh = decrypt_token(oauth_token.encrypted_refresh_token)

        if not access or oauth_token.expires_at is None:
            raise WeeztixAuthenticationError("Opgeslagen Weeztix-token is onvolledig.")

        return WeeztixTokenData(access, refresh_token=refresh or None, token_type=oauth_token.token_type or "Bearer", expires_at=oauth_token.expires_at, refresh_token_expires_at=(oauth_token.refresh_token_expires_at))

    @staticmethod
    def save_token(oauth_token: WeeztixOAuthToken, token: WeeztixTokenData) -> None:
        oauth_token.encrypted_access_token = encrypt_token(token.access_token)
        oauth_token.encrypted_refresh_token = encrypt_token(token.refresh_token)
        oauth_token.token_type = token.token_type
        oauth_token.expires_at = token.expires_at
        oauth_token.refresh_token_expires_at = token.refresh_token_expires_at
        oauth_token.save(update_fields=["encrypted_access_token", "encrypted_refresh_token", "token_type", "expires_at", "refresh_token_expires_at", "updated_at"])

    @transaction.atomic
    def save_for_user(self, *, user, token: WeeztixTokenData, scope: str = "") -> WeeztixOAuthToken:
        if user is None or not getattr(user, "is_authenticated", False):
            raise WeeztixAuthenticationError(
                "Er is geen ingelogde gebruiker beschikbaar."
            )

        oauth_token, _ = (
            WeeztixOAuthToken.objects
            .select_for_update()
            .get_or_create(
                user=user,
                defaults={
                    "encrypted_access_token": "",
                    "encrypted_refresh_token": "",
                },
            )
        )

        oauth_token.encrypted_access_token = encrypt_token(
            token.access_token
        )

        oauth_token.encrypted_refresh_token = encrypt_token(
            token.refresh_token
        )

        oauth_token.token_type = token.token_type
        oauth_token.scope = scope
        oauth_token.expires_at = token.expires_at
        oauth_token.refresh_token_expires_at = (
            token.refresh_token_expires_at
        )

        oauth_token.save(
            update_fields=[
                "encrypted_access_token",
                "encrypted_refresh_token",
                "token_type",
                "scope",
                "expires_at",
                "refresh_token_expires_at",
                "updated_at",
            ]
        )

        return oauth_token

    @staticmethod
    def from_response(data: dict[str, Any]) -> WeeztixTokenData:
        try:
            access_token = str(data["access_token"])
            expires_in = int(data["expires_in"])
        except (KeyError, TypeError, ValueError) as exc:
            raise WeeztixResponseError("Ongeldige Weeztix-tokenresponse.") from exc
        now = datetime.now(timezone.utc)
        refresh_seconds = data.get("refresh_token_expires_in")

        try:
            refresh_expires_at = (
                    now + timedelta(seconds=(refresh_seconds))
                    if refresh_seconds is not None
                    else None
            )
        except (TypeError, ValueError) as exc:
            raise WeeztixResponseError(
                "Ongeldige geldigheidsduur van het Weeztix-refresh-token."
            ) from exc

        refresh_token = data.get("refresh_token")

        return WeeztixTokenData( access_token=access_token, refresh_token=(str(refresh_token) if refresh_seconds else None), token_type=str(data.get("token_type")or "Bearer"), expires_at=now + timedelta(seconds=expires_in), refresh_token_expires_at=refresh_expires_at)

    def _post_token_request(
        self, *, payload: dict[str, str], connection_error: str, authentication_error: str, response_error: str) -> WeeztixTokenData:
        _, _, token_url = self._oauth_settings()

        try:
            response = self.session.post(token_url, json=payload, headers={"Accept": "application/json"}, timeout=30)

        except requests.RequestException as exc:
            raise WeeztixConnectionError(connection_error) from exc

        if not response.ok:
            raise WeeztixAuthenticationError(
                f"{authentication_error} "
                f"HTTP {response.status_code}: {response.text}"
            )

        try:
            response_data = response.json()
        except ValueError as exc:
            raise WeeztixResponseError(response_error) from exc

        if not isinstance(response_data, dict):
            raise WeeztixResponseError(response_error)

        return self.from_response(response_data)

    def exchange_authorization_code(self, *, code: str, redirect_uri: str) -> WeeztixTokenData:
        if not code:
            raise WeeztixAuthenticationError(
                "De Weeztix authorization code ontbreekt."
            )
        if not redirect_uri:
            raise WeeztixAuthenticationError(
                "De Weeztix redirect URI ontbreekt."
            )

        client_id, client_secret, _ = self._oauth_settings()
        token = self._post_token_request(
            payload={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
            },
            connection_error=(
                "De Weeztix authorization code kon niet worden "
                "omgewisseld."
            ),
            authentication_error=(
                "Omwisselen van de Weeztix authorization code "
                "is mislukt."
            ),
            response_error=(
                "Weeztix gaf bij de OAuth-callback geen geldige "
                "JSON-response terug."
            ),
        )

        if not token.refresh_token:
            raise WeeztixResponseError(
                "Weeztix heeft geen refresh-token teruggegeven."
            )

        return token

    def refresh(self, refresh_token: str) -> WeeztixTokenData:
        if not refresh_token:
            raise WeeztixAuthenticationError(
                "Het Weeztix-refresh-token ontbreekt."
            )

        client_id, client_secret, _ = self._oauth_settings()
        token = self._post_token_request(
            payload={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            connection_error=(
                "Token-refresh kon Weeztix niet bereiken."
            ),
            authentication_error="Token-refresh is mislukt.",
            response_error=(
                "Token-refresh gaf geen geldige JSON-response."
            ),
        )

        if not token.refresh_token:
            raise WeeztixResponseError(
                "Token-refresh gaf geen nieuw refresh-token."
            )

        return token

