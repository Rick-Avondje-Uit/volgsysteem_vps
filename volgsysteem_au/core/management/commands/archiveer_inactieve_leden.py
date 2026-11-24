from datetime import timedelta

from django.core.management import CommandParser
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Deelnemer, Ticket, Activiteit


class Command(BaseCommand):
    help = (
        "Archiveert deelnemers zonder tickets of deelnemers waarvan het laatste ticket ouder is dan 365 dagen"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action="store_true",
            help="Toont welke deelnemers zouden worden gearchiveerd zonder wijzigingen op te slaan.",
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        grens_datum = timezone.now() - timedelta(days=365)
        deelnemers = Deelnemer.objects.all()
        aantal_gearchiveerd = 0

        for deelnemer in deelnemers:
            laatste_ticket = (
                Ticket.objects.filter(deelnemer=deelnemer)
                .order_by("activiteit__begin_datum")
                .last()
            )

            reden = None

            if laatste_ticket is None:
                reden = "geen tickets"

            elif laatste_ticket.activiteit.begin_datum < grens_datum:
                reden = "laatste ticket ouder dan 365 dagen"

            if reden is None:
                continue

            aantal_gearchiveerd += 1

            self.stdout.write(
                f"{deelnemer}: {reden}"
            )

            if not dry_run:
                deelnemer.gearchiveerd = True
                deelnemer.save(
                    update_fields=["gearchiveerd"]
                )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry-run: {aantal_gearchiveerd} deelnemers zouden worden gearchiveerd"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"{aantal_gearchiveerd} deelnemers geachiveerd."
                )
            )


