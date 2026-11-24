from datetime import date
from django import forms
from django.test import TestCase
from core.models import Deelnemer, Plaats

class DeelnemerModelTest(TestCase):

    def setUp(self):
        self.aanmeld_locatie = Plaats.objects.create(naam="Tilburg", )

        self.deelnemer1 = Deelnemer.objects.create(naam="Rico Lammers", aanmeld_locatie=self.aanmeld_locatie, )
        self.deelnemer2 = Deelnemer.objects.create(naam="Rico van Hoeven", geboortedatum="1995-04-02",
                                                   aanmeld_locatie=self.aanmeld_locatie, )
        self.deelnemer3 = Deelnemer.objects.create(naam="Rico van der Hoeven", aanmeld_locatie=self.aanmeld_locatie, )
        self.deelnemer4 = Deelnemer(naam="Rico van Hoeven", geboortedatum="1995-02-30",
                                    aanmeld_locatie=self.aanmeld_locatie, )

    def test_first_name_correct(self):
        self.assertEqual(self.deelnemer1.voornaam, "Rico")
        self.assertEqual(self.deelnemer2.voornaam, "Rico")
        self.assertEqual(self.deelnemer3.voornaam, "Rico")

    def test_last_name_correct(self):
        self.assertEqual(self.deelnemer1.achternaam, "Lammers")
        self.assertEqual(self.deelnemer2.achternaam, "Hoeven")
        self.assertEqual(self.deelnemer3.achternaam, "Hoeven")

    def test_tussenvoegsel_correct(self):
        self.assertIsNone(self.deelnemer1.tussenvoegsel)
        self.assertEqual(self.deelnemer2.tussenvoegsel, "van")
        self.assertEqual(self.deelnemer3.tussenvoegsel, "van der")

    def test_geboortedatum_correct(self):
        self.deelnemer1.refresh_from_db()
        self.deelnemer2.refresh_from_db()
        self.assertIsNone(self.deelnemer1.geboortedatum)
        self.assertEqual(self.deelnemer2.geboortedatum, date(1995, 0o4, 0o2))

    def test_ongeldige_datum_afgevangen(self):
        with self.assertRaises(forms.ValidationError):
            self.deelnemer4.full_clean()