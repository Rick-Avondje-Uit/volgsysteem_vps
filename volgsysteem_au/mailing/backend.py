from __future__ import annotations

import threading
from email.message import MIMEPart
from email.utils import parseaddr
from io import BytesIO
from pathlib import Path
from typing import Any

from O365 import Account
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address


class O365Exception(Exception):
    """Raised when authentication or delivery through Microsoft 365 fails."""


class O365EmailBackend(BaseEmailBackend):
    """Send Django EmailMessage objects through Microsoft Graph/O365."""

    def __init__(
            self,
            tenant_id: str | None = None,
            client_id: str | None = None,
            client_secret: str | None = None,
            sender: str | None = None,
            fail_silently: bool = False,
            **kwargs: Any,
    ) -> None:
        # Django 6.1 passes the mailer alias in kwargs. BaseEmailBackend must
        # receive it, while this backend handles fail_silently itself.
        super().__init__(**kwargs)
        self.tenant_id = tenant_id or getattr(settings, "EMAIL_O365_TENANT_ID", None)
        self.client_id = client_id or getattr(settings, "EMAIL_O365_CLIENT_ID", None)
        self.client_secret = client_secret or getattr(
            settings, "EMAIL_O365_CLIENT_SECRET", None
        )
        self.sender = sender or getattr(settings, "EMAIL_O365_SENDER", None)
        self.fail_silently = fail_silently
        self.account: Account | None = None
        self.mailbox = None
        self._lock = threading.RLock()

    def open(self) -> bool:
        """Authenticate and initialize the configured sender mailbox."""
        if self.mailbox is not None:
            return False

        missing = [
            name
            for name, value in (
                ("tenant_id", self.tenant_id),
                ("client_id", self.client_id),
                ("client_secret", self.client_secret),
                ("sender", self.sender),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"Missing O365 configuration: {', '.join(missing)}")

        self.account = Account(
            (self.client_id, self.client_secret),
            auth_flow_type="credentials",
            tenant_id=self.tenant_id,
        )
        if not self.account.authenticate():
            self.account = None
            raise O365Exception("O365 authentication failed.")

        self.mailbox = self.account.mailbox(resource=self.sender)
        return True

    def close(self) -> None:
        """Release locally held O365 objects."""
        self.mailbox = None
        self.account = None

    def send_messages(self, email_messages) -> int:
        """Send a collection of Django email messages and return the count."""
        if not email_messages:
            return 0

        with self._lock:
            try:
                self.open()
                return sum(bool(self._send(message)) for message in email_messages)
            except Exception:
                if self.fail_silently:
                    return 0
                raise
            finally:
                self.close()

    @staticmethod
    def _sanitize_addresses(addresses, encoding: str) -> list[str]:
        return [sanitize_address(address, encoding) for address in addresses]

    @staticmethod
    def _alternative_parts(email_message) -> list[tuple[Any, str]]:
        parts: list[tuple[Any, str]] = []
        for alternative in getattr(email_message, "alternatives", ()):
            if hasattr(alternative, "content") and hasattr(alternative, "mimetype"):
                parts.append((alternative.content, alternative.mimetype))
            else:
                content, mimetype = alternative
                parts.append((content, mimetype))
        return parts

    @staticmethod
    def _attachment_parts(attachment) -> tuple[str, bytes, str] | None:
        if hasattr(attachment, "filename") and hasattr(attachment, "content"):
            filename = attachment.filename
            content = attachment.content
            mimetype = attachment.mimetype
        elif isinstance(attachment, tuple) and len(attachment) == 3:
            filename, content, mimetype = attachment
        else:
            return None

        if isinstance(content, str):
            content = content.encode("utf-8")
        elif isinstance(content, BytesIO):
            content = content.getvalue()
        elif not isinstance(content, bytes):
            content = bytes(content)
        return str(filename), content, str(mimetype or "application/octet-stream")

    def _send(self, email_message) -> bool:
        """Send one Django EmailMessage through the active mailbox."""
        if not email_message.recipients():
            return False
        if self.mailbox is None:
            raise O365Exception("O365 mailbox is not open.")

        encoding = email_message.encoding or settings.DEFAULT_CHARSET
        sanitized_from = sanitize_address(email_message.from_email, encoding)
        _, from_address = parseaddr(sanitized_from)
        if from_address and from_address.casefold() != str(self.sender).casefold():
            raise O365Exception(
                "The message from_email must match the configured O365 sender."
            )

        try:
            message = self.mailbox.new_message()
            message.to.add(self._sanitize_addresses(email_message.to, encoding))
            if email_message.cc:
                message.cc.add(self._sanitize_addresses(email_message.cc, encoding))
            if email_message.bcc:
                message.bcc.add(self._sanitize_addresses(email_message.bcc, encoding))
            if email_message.reply_to:
                message.reply_to.add(
                    self._sanitize_addresses(email_message.reply_to, encoding)
                )

            message.subject = email_message.subject
            html_body = next(
                (
                    content
                    for content, mimetype in self._alternative_parts(email_message)
                    if mimetype == "text/html"
                ),
                None,
            )
            message.body = html_body if html_body is not None else email_message.body
            message.body_type = "HTML" if html_body is not None else "Text"

            for attachment in getattr(email_message, "attachments", ()):
                if isinstance(attachment, (str, Path)):
                    message.attachments.add(str(attachment))
                    continue
                if isinstance(attachment, MIMEPart):
                    filename = attachment.get_filename()
                    if not filename:
                        raise ValueError("A MIMEPart attachment must have a filename.")
                    payload = attachment.get_payload(decode=True) or b""
                    message.attachments.add([(BytesIO(payload), filename)])
                    continue
                parsed = self._attachment_parts(attachment)
                if parsed is None:
                    raise TypeError(f"Unsupported attachment type: {type(attachment)!r}")
                filename, content, _mimetype = parsed
                message.attachments.add([(BytesIO(content), filename)])

            message.send()
            return True
        except Exception:
            if self.fail_silently:
                return False
            raise
