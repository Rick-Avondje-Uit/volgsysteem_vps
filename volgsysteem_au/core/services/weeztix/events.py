from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from django.conf import settings
from .client import WeeztixClient
from .exceptions import WeeztixResponseError

BASE = settings.WEEZTIX_API_BASE_URL.rstrip("/")
ENDPOINT = f"{BASE}/events"

@dataclass(frozen=True)
class WeeztixEvent:
    guid: str
    name: str
    start: datetime | None = None
    end: datetime | None = None
    raw: dict[str, Any] | None = None

class WeeztixEventService:
    def __init__(self, *, user=None, client=None):
        if client is None and user is None: raise ValueError("Geef user of client op.")
        self.client = client or WeeztixClient.from_user(user)

    @staticmethod
    def _url(guid):
        guid=str(guid).strip()
        if not guid: raise ValueError("Event-GUID ontbreekt.")
        if guid.startswith(("http://","https://")): return guid
        if guid.startswith("/"): return f"{BASE}{guid}"
        if guid.startswith("events/"): return f"{BASE}/{guid}"
        return f"{ENDPOINT}/{guid}"

    @staticmethod
    def _dt(value):
        if not value: return None
        if isinstance(value, datetime): return value
        try: return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError: return None

    def get(self, guid):
        data=self.client.get(self._url(guid))
        if not isinstance(data, dict) or not data.get("guid") or not data.get("name"):
            raise WeeztixResponseError("Ongeldige eventresponse.")
        return WeeztixEvent(str(data["guid"]), str(data["name"]), self._dt(data.get("start") or data.get("starts_at")), self._dt(data.get("end") or data.get("ends_at")), data)

    def get_many(self, guids): return [self.get(g) for g in dict.fromkeys(str(x).strip() for x in guids if str(x).strip())]
    def exists(self, guid): return bool(self.get(guid).guid)
