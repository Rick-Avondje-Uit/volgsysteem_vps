from datetime import datetime
from django.test import TestCase
from django.utils import timezone
from core.models import Activiteit, Deelnemer, Plaats, Ticket


class TicketModelTest(TestCase):
    def setUp(self):
        begin_datum = datetime(2023, 12, 5, 12, 0, 0)
        eind_datum = datetime(2023, 12, 5, 13, 15, 0)

        begin_datum = timezone.make_aware(begin_datum)
        eind_datum = timezone.make_aware(eind_datum)

        self.plaats = Plaats.objects.create(
            naam="Tilburg",
        )

        self.deelnemer = Deelnemer.objects.create(
            naam="Rico Lammers",
            aanmeld_locatie=self.plaats,
        )

        self.activiteit = Activiteit.objects.create(
            guid="blablabla",
            naam="test activiteit",
            begin_datum=begin_datum,
            eind_datum=eind_datum,
            plaats=self.plaats,
        )

        self.ticket1 = Ticket.objects.create(
            activiteit=self.activiteit,
            deelnemer=self.deelnemer,
            bedrag=1.23,
        )

    def test_deelnemer_correct(self):
        self.assertEqual(self.ticket1.deelnemer, self.deelnemer)

    def test_activiteit_correct(self):
        self.assertEqual(self.ticket1.activiteit, self.activiteit)

    def test_ticket_blijft_bestaan_als_deelnemer_verwijderd(self):
        self.assertEqual(Ticket.objects.count(), 1)
        self.deelnemer.delete()
        self.assertEqual(Ticket.objects.count(), 1)
        ticket = Ticket.objects.get()
        self.assertIsNone(ticket.deelnemer)

    def test_ticket_blijft_bestaan_als_activiteit_verwijderd(self):
        self.assertEqual(Ticket.objects.count(), 1)
        self.activiteit.delete()
        self.assertEqual(Ticket.objects.count(), 0)

    def test_reguliere_ticket_standaard_ingesteld(self):
        self.assertEqual(self.ticket1.get_type_ticket_display(), "Reguliere ticket")