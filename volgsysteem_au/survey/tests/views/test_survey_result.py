from django.urls.base import reverse

from survey.tests.management.test_management import TestManagement


class TestSurveyResult(TestManagement):
    def test_survey_result(self):
        """We need logging for survey result if the survey need login."""
        url = reverse("survey-result", args=(2,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Survey 1 vereist authenticatie
        response = self.client.get(reverse("survey-result", args=(1,)))
        self.assertEqual(response.status_code, 302)
        # Survey 4 leidt zonder ingelogde gebruiker naar de loginpagina
        response = self.client.get(reverse("survey-result", args=(4,)), follow=True,)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,"Inloggen")
        self.login()
        response = self.client.get(reverse("survey-result", args=(2,)))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("survey-result", args=(1,)))
        self.assertEqual(response.status_code, 200)
