from django.test import TestCase

class ProtectedViewTests(TestCase):

    def test_anonymous_user_cannot_access_deelnemers(self):
        response = self.client.get("/deelnemers/")

        self.assertNotEqual(response.status_code, 200)