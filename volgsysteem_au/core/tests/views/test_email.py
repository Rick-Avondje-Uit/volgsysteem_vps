from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="noreply@avondjeuit.org",
)
class TestEmailViewTests(TestCase):
    def setUp(self):
        self.url = reverse("core:test_email")

    def test_get_toont_emailformulier(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "registration/test_email_form.html",
        )
        self.assertIn("form", response.context)

    def test_get_verstuurt_geen_email(self):
        self.client.get(self.url)

        self.assertEqual(len(mail.outbox), 0)

    def test_geldige_post_verstuurt_email(self):
        response = self.client.post(
            self.url,
            {
                "email": "test@example.com",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(
            email.subject,
            "Test email volgsysteem 2.0",
        )
        self.assertEqual(
            email.from_email,
            "noreply@avondjeuit.org",
        )
        self.assertEqual(
            email.to,
            ["test@example.com"],
        )
        self.assertEqual(
            email.body,
            (
                "Hallo\n"
                "Als je dit leest werkt de mail functie naar behoren.\n"
                "Met vriendelijke groet Team Avondje Uit."
            ),
        )

    def test_geldige_post_toont_succesmelding(self):
        response = self.client.post(
            self.url,
            {
                "email": "test@example.com",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Email is als het goed is verzonden.",
        )

    def test_ongeldig_emailadres_verstuurt_geen_email(self):
        response = self.client.post(
            self.url,
            {
                "email": "geen-geldig-emailadres",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_ongeldig_emailadres_toont_formulier_opnieuw(self):
        response = self.client.post(
            self.url,
            {
                "email": "geen-geldig-emailadres",
            },
        )

        self.assertTemplateUsed(
            response,
            "registration/test_email_form.html",
        )
        self.assertIn("form", response.context)

    def test_leeg_emailadres_verstuurt_geen_email(self):
        response = self.client.post(
            self.url,
            {
                "email": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_meerdere_requests_versturen_afzonderlijke_emails(self):
        self.client.post(
            self.url,
            {
                "email": "eerste@example.com",
            },
        )

        self.client.post(
            self.url,
            {
                "email": "tweede@example.com",
            },
        )

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].to,
            ["eerste@example.com"],
        )
        self.assertEqual(
            mail.outbox[1].to,
            ["tweede@example.com"],
        )

    def test_leeg_emailadres_bevat_validatiefout(self):
        response = self.client.post(
            self.url,
            {
                "email": "",
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context["form"]

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertTrue(form["email"].errors)

        self.assertEqual(len(mail.outbox), 0)