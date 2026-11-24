# core/services/weeztix/tickets.py

import logging

from django.db import transaction

from .client import WeeztixClient

logger = logging.getLogger(__name__)


class WeeztixTicketService:
    def __init__(self):
        self.client = WeeztixClient()

    def get_tickets(self, *, event_id=None):
        """
        Haal tickets op uit Weeztix.

        Endpoint moet worden ingesteld op basis van het
        daadwerkelijke Weeztix ticket/order endpoint.
        """

        url = "WEEZTIX_TICKET_ENDPOINT"

        params = {}

        if event_id:
            params["event_id"] = event_id

        return self.client.get(
            url,
            params=params,
        )

    @transaction.atomic
    def import_tickets(self, *, event_id=None):
        data = self.get_tickets(event_id=event_id)

        if not data:
            return {
                "found": 0,
                "created": 0,
                "updated": 0,
                "skipped": 0,
            }

        created = 0
        updated = 0
        skipped = 0

        for ticket_data in data:

            try:
                result = self._import_ticket(ticket_data)

                if result == "created":
                    created += 1
                elif result == "updated":
                    updated += 1
                else:
                    skipped += 1

            except Exception:
                logger.exception(
                    "Fout tijdens importeren Weeztix-ticket: %s",
                    ticket_data,
                )
                raise

        return {
            "found": len(data),
            "created": created,
            "updated": updated,
            "skipped": skipped,
        }

    def _import_ticket(self, ticket_data):
        """
        Zet een Weeztix-ticket om naar een lokaal Django-model.
        """

        ticket_guid = ticket_data.get("guid")

        if not ticket_guid:
            logger.warning(
                "Ticket zonder GUID overgeslagen: %s",
                ticket_data,
            )
            return "skipped"

        # Hier komt de mapping naar jouw echte Ticket-model.
        #
        # Bijvoorbeeld:
        #
        # ticket, created = Ticket.objects.update_or_create(
        #     weeztix_guid=ticket_guid,
        #     defaults={
        #         ...
        #     },
        # )
        #
        # return "created" if created else "updated"

        logger.debug(
            "Weeztix-ticket ontvangen: %s",
            ticket_guid,
        )

        return "skipped"