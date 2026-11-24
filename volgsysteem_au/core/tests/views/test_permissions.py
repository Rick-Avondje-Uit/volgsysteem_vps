from django.contrib.auth.models import User
from django.test import TestCase, Client

class AdminOnlyPageTest(TestCase):
    def setUp(self):
        # Maak een admingebruiker aan
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpassword',
            is_staff=True,  # Markeer als admingebruiker
        )

        # Maak een gewone gebruiker aan (geen admin)
        self.regular_user = User.objects.create_user(
            username='user',
            password='userpassword',
        )

    def test_admin_only_page(self):
        # Creëer een testclient
        client = Client()

        # Probeer toegang te krijgen tot de pagina als niet-ingelogde gebruiker
        response = client.get('/deelnemers/')
        self.assertEqual(response.status_code, 302)  # 302 is de code voor omleiding (loginpagina)

        # Log in als een gewone gebruiker
        client.login(username='user', password='userpassword')

        # Probeer toegang te krijgen tot de pagina als een gewone gebruiker
        response = client.get('/deelnemers/')
        self.assertEqual(response.status_code, 403)  # gewone gebruiker heeft geen recht hiertoe dus krijgt permission error

        # Log in als een admingebruiker
        client.login(username='admin', password='adminpassword')

        # Probeer toegang te krijgen tot de pagina als een admingebruiker
        response = client.get('/deelnemers/')
        self.assertEqual(response.status_code, 200)  # 200 is de code voor een succesvolle aanvraag