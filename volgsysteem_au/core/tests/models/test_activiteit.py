from datetime import date, datetime
from django import forms
from django.test import TestCase
from django.utils import timezone
from core.models import Activiteit, Plaats


class ActiviteitModelTest(TestCase):
    def setUp(self):
        begin_datum = datetime(2023, 12, 5, 12, 0, 0)
        eind_datum = datetime(2023, 12, 5, 13, 15, 0)
        begin_datum = timezone.make_aware(begin_datum)
        eind_datum = timezone.make_aware(eind_datum)
        self.plaats = Plaats.objects.create(naam="Tilburg")
        self.activiteit1 = Activiteit.objects.create(guid="blablabla", begin_datum=begin_datum, eind_datum=eind_datum,
                                                     plaats=self.plaats)
        self.activiteit2_zonder_plaats = Activiteit(
            **{"guid": "blablabla2", "begin_datum": begin_datum, "eind_datum": eind_datum})
        self.activiteit_vakantie = Activiteit.objects.create(guid="blablabla3", begin_datum=begin_datum,
                                                             eind_datum=eind_datum, plaats=self.plaats,
                                                             type_activiteit="vakantie")

    def test_tijdsduur_correct(self):
        self.assertTrue(self.activiteit1.tijdsduur_uren, 1.25)

    def test_activiteit_default_correct(self):
        self.assertTrue(self.activiteit1.type_activiteit, "activiteit")
        self.assertTrue(self.activiteit_vakantie.type_activiteit, "vakantie")

    def test_plaats_valide(self):
        self.assertEqual(self.activiteit1.plaats, self.plaats)

    def test_ongeldige_plaats_afgevangen(self):
        with self.assertRaises(forms.ValidationError):
            self.activiteit2_zonder_plaats.full_clean()

    def test_property_jaar_correct(self):
        self.assertEqual(self.activiteit1.jaar, 2023)

    def test_property_maand_correct(self):
        self.assertEqual(self.activiteit1.maand, 12)

    def test_property_jaar_correct(self):
        self.assertEqual(self.activiteit1.dag, 5)

    def test_property_datum_correct(self):
        self.assertEqual(self.activiteit1.datum, date(2023, 12, 5))