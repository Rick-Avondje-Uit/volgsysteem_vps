from email.message import MIMEPart
from io import BytesIO
from unittest.mock import MagicMock, patch
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.test import SimpleTestCase, override_settings
from mailing.backend import O365EmailBackend, O365Exception

MAILERS = {
    "default": {
        "BACKEND": "django_o365.backend.O365EmailBackend",
        "OPTIONS": {
            "tenant_id": "tenant",
            "client_id": "client",
            "client_secret": "secret",
            "sender": "sender@example.com",
        },
    }
}


@override_settings(MAILERS=MAILERS, DEFAULT_CHARSET="utf-8")
class O365EmailBackendTests(SimpleTestCase):
    def make_backend(self, **overrides):
        options = {
            "tenant_id": "tenant",
            "client_id": "client",
            "client_secret": "secret",
            "sender": "sender@example.com",
        }
        options.update(overrides)
        return O365EmailBackend(**options)

    def configure_account(self, mock_account_cls):
        account = mock_account_cls.return_value
        account.authenticate.return_value = True
        mailbox = account.mailbox.return_value
        graph_message = mailbox.new_message.return_value
        return account, mailbox, graph_message

    @patch("mailing.backend.Account")
    def test_send_simple_email(self, account_cls):
        account, mailbox, graph_message = self.configure_account(account_cls)
        backend = self.make_backend(alias="default")
        email = EmailMessage(
            "Test Subject", "Test Body", "sender@example.com", ["to@example.com"]
        )

        self.assertEqual(backend.send_messages([email]), 1)
        account_cls.assert_called_once_with(
            ("client", "secret"), auth_flow_type="credentials", tenant_id="tenant"
        )
        account.authenticate.assert_called_once_with()
        account.mailbox.assert_called_once_with(resource="sender@example.com")
        graph_message.to.add.assert_called_once_with(["to@example.com"])
        self.assertEqual(graph_message.subject, "Test Subject")
        self.assertEqual(graph_message.body, "Test Body")
        self.assertEqual(graph_message.body_type, "Text")
        graph_message.send.assert_called_once_with()
        self.assertIsNone(backend.mailbox)

    @patch("mailing.backend.Account")
    def test_html_cc_bcc_and_reply_to(self, account_cls):
        _, _, graph_message = self.configure_account(account_cls)
        backend = self.make_backend()
        email = EmailMultiAlternatives(
            "HTML",
            "Plain",
            "sender@example.com",
            ["to@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            reply_to=["reply@example.com"],
        )
        email.attach_alternative("<p>HTML</p>", "text/html")

        self.assertEqual(backend.send_messages([email]), 1)
        graph_message.cc.add.assert_called_once_with(["cc@example.com"])
        graph_message.bcc.add.assert_called_once_with(["bcc@example.com"])
        graph_message.reply_to.add.assert_called_once_with(["reply@example.com"])
        self.assertEqual(graph_message.body, "<p>HTML</p>")
        self.assertEqual(graph_message.body_type, "HTML")

    @patch("mailing.backend.Account")
    def test_byte_attachment(self, account_cls):
        _, _, graph_message = self.configure_account(account_cls)
        email = EmailMessage(
            "Attachment", "Body", "sender@example.com", ["to@example.com"]
        )
        email.attach("report.txt", b"content", "text/plain")

        self.assertEqual(self.make_backend().send_messages([email]), 1)
        attachment_list = graph_message.attachments.add.call_args.args[0]
        content, filename = attachment_list[0]
        self.assertIsInstance(content, BytesIO)
        self.assertEqual(content.read(), b"content")
        self.assertEqual(filename, "report.txt")

    @patch("mailing.backend.Account")
    def test_mimepart_attachment(self, account_cls):
        _, _, graph_message = self.configure_account(account_cls)
        part = MIMEPart()
        part.set_content(b"pdf-bytes", maintype="application", subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename="report.pdf")
        email = EmailMessage(
            "Attachment", "Body", "sender@example.com", ["to@example.com"]
        )
        email.attach(part)

        self.assertEqual(self.make_backend().send_messages([email]), 1)
        content, filename = graph_message.attachments.add.call_args.args[0][0]
        self.assertEqual(content.read(), b"pdf-bytes")
        self.assertEqual(filename, "report.pdf")

    def test_no_recipients_returns_false(self):
        backend = self.make_backend()
        backend.mailbox = MagicMock()
        email = EmailMessage("Subject", "Body", "sender@example.com", [])
        self.assertFalse(backend._send(email))

    def test_missing_configuration(self):
        backend = self.make_backend(client_secret="")
        backend.client_secret = None
        with self.assertRaisesRegex(ValueError, "client_secret"):
            backend.open()

    @patch("mailing.backend.Account")
    def test_authentication_failure(self, account_cls):
        account_cls.return_value.authenticate.return_value = False
        with self.assertRaises(O365Exception):
            self.make_backend().open()

    @patch("mailing.backend.Account")
    def test_sender_mismatch_is_rejected(self, account_cls):
        self.configure_account(account_cls)
        email = EmailMessage(
            "Subject", "Body", "other@example.com", ["to@example.com"]
        )
        with self.assertRaisesRegex(O365Exception, "must match"):
            self.make_backend().send_messages([email])

    @patch("mailing.backend.Account")
    def test_fail_silently_returns_zero(self, account_cls):
        account_cls.return_value.authenticate.side_effect = RuntimeError("Graph down")
        result = self.make_backend(fail_silently=True).send_messages(
            [EmailMessage("Subject", "Body", "sender@example.com", ["to@example.com"])]
        )
        self.assertEqual(result, 0)
