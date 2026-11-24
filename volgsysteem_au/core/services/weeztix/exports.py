from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings

from .client import WeeztixClient
from .exceptions import (
    WeeztixExportError,
    WeeztixExportNotReady,
)


BASE = settings.WEEZTIX_API_BASE_URL.rstrip("/")
ENDPOINT = f"{BASE}/export"


@dataclass(frozen=True)
class WeeztixExport:
    guid: str
    download_url: str | None = None
    raw: dict[str, Any] | None = None

    @property
    def is_ready(self) -> bool:
        return bool(self.download_url)


class WeeztixExportService:
    def __init__(self, *, user=None, client=None):
        if client is None and user is None:
            raise ValueError("Geef user of client op.")

        self.client = client or WeeztixClient.from_user(user)

    @staticmethod
    def _url(guid: str) -> str:
        guid = str(guid).strip()

        if not guid:
            raise WeeztixExportError("Export-GUID ontbreekt.")

        if guid.startswith(("http://", "https://")):
            return guid

        if guid.startswith("/"):
            return f"{BASE}{guid}"

        if guid.startswith("export/"):
            return f"{BASE}/{guid}"

        return f"{ENDPOINT}/{guid}"

    def start(
        self,
        *,
        event_ids,
        name="Ticketexport Avondje Uit",
        description="Ticketexport voor Avondje Uit",
    ) -> WeeztixExport:
        if not event_ids:
            raise WeeztixExportError(
                "Selecteer minimaal één activiteit."
            )

        data = self.client.post(
            ENDPOINT,
            json={
                "name": name,
                "description": description,
                "type": "orders_and_order_tickets",
                "timezone": "Europe/Amsterdam",
                "filetypes": ["xlsx"],
                "events": event_ids,
            },
        )

        if not isinstance(data, dict) or not data.get("guid"):
            raise WeeztixExportError(
                "Weeztix gaf geen export-GUID terug."
            )

        return WeeztixExport(
            guid=str(data["guid"]),
            raw=data,
        )

    def get(self, guid: str) -> WeeztixExport:
        data = self.client.get(self._url(guid))

        if not isinstance(data, dict):
            raise WeeztixExportError(
                "Ongeldige exportresponse."
            )

        links = data.get("download_links") or {}

        download_url = (
            links.get("xlsx")
            if isinstance(links, dict)
            else None
        )

        return WeeztixExport(
            guid=str(guid),
            download_url=download_url,
            raw=data,
        )

    def download_xlsx(self, guid: str) -> bytes:
        export = self.get(guid)

        if not export.download_url:
            raise WeeztixExportNotReady(
                "Export is nog niet gereed."
            )

        try:
            response = requests.get(
                export.download_url,
                timeout=30,
            )
            response.raise_for_status()

        except requests.RequestException as exc:
            raise WeeztixExportError(
                "De Weeztix XLSX-export kon niet worden gedownload."
            ) from exc

        return response.content

    def delete(self, guid: str) -> None:
        self.client.delete(self._url(guid))