from django.core.management.base import BaseCommand, CommandError
from core.services.weeztix.exceptions import WeeztixAPIError, WeeztixAuthenticationError
from core.services.weeztix.tickets import WeeztixTicketService


class Command(BaseCommand):
    help = "Importeer tickets vanuit Weeztix."

    def add_arguments(self, parser):
        parser.add_argument(
            "--event-id",
            dest="event_id",
            help="Importeer alleen tickets van dit Weeztix-event.",
        )

    def handle(self, *args, **options):
        event_id = options.get("event_id")

        self.stdout.write(
            "Tickets ophalen uit Weeztix..."
        )

        service = WeeztixTicketService()

        try:
            result = service.import_tickets(
                event_id=event_id,
            )

        except WeeztixAuthenticationError as exc:
            raise CommandError(
                f"Weeztix-authenticatie mislukt: {exc}"
            ) from exc

        except WeeztixAPIError as exc:
            raise CommandError(
                f"Weeztix API-fout: {exc}"
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                "Weeztix-import voltooid\n"
                f"Gevonden: {result['found']}\n"
                f"Nieuw: {result['created']}\n"
                f"Bijgewerkt: {result['updated']}\n"
                f"Overgeslagen: {result['skipped']}"
            )
        )