import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlencode
from django.db.models import Count, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DeleteView, DetailView, ListView, UpdateView
from core.forms import ActiviteitenFormSet
from core.models import Activiteit, Plaats, Ticket
from core.permissions import is_begeleider_required
from core.utils.dates import format_dutch_date, parse_dutch_date_range
from core.services.weeztix.client import WeeztixClient
from core.services.weeztix.exceptions import WeeztixAPIError
from core.views import deelnemer

logger = logging.getLogger(__name__)

@method_decorator(is_begeleider_required, name='dispatch')
class ActiviteitListView(ListView):

    template_name = 'core/activiteit/activiteit_list.html'
    model = Activiteit
    ordering = ['-datum', 'plaats']
    context_object_name = "activiteiten"

    def get_queryset(self) -> QuerySet[Any]:
        queryset = Activiteit.objects.annotate(aantal_tickets=Count('ticket', distinct=True)).order_by("-begin_datum")
        return queryset


@method_decorator(is_begeleider_required, name="dispatch")
class ActiviteitToevoegenView(View):
    template_name = "core/activiteit/activiteit_add.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        start_date, end_date = parse_dutch_date_range(
            request.GET.get("start_date"),
            request.GET.get("end_date"),
        )

        print("START DATE:", start_date, type(start_date))
        print("END DATE:", end_date, type(end_date))

        client = WeeztixClient.from_user(request.user)

        try:
            events = self._get_events(client)
            print("WEEZTIX EVENTS:", events)
            print("AANTAL WEEZTIX EVENTS:", len(events))
            events = self._exclude_imported_events(events)
            print("NA EXCLUDE IMPORTED:", len(events))
            events = self._filter_events_by_date(
                events=events,
                start_date=start_date,
                end_date=end_date,
            )
            print("NA DATUMFILTER:", len(events))
            print("GEFILTERDE EVENTS:", events)
            initial_data = self._build_initial_data(client=client, events=events)
            print("AANTAL INITIAL DATA:", len(initial_data))
            print("INITIAL DATA:", initial_data)

        except WeeztixAPIError:
            logger.exception(
                "Weeztix-activiteiten konden niet worden opgehaald."
            )

            formset = ActiviteitenFormSet(initial=[])

            return render(
                request,
                self.template_name,
                {
                    "formset": formset,
                    "start_date": request.GET.get("start_date", ""),
                    "end_date": request.GET.get("end_date", ""),
                    "error": (
                        "De activiteiten konden niet bij Weeztix worden "
                        "opgehaald. Probeer het later opnieuw."
                    ),
                },
            )

        except (TypeError, ValueError):
            logger.exception(
                "Een Weeztix-event bevat ongeldige gegevens."
            )

            formset = ActiviteitenFormSet(initial=[])

            return render(
                request,
                self.template_name,
                {
                    "formset": formset,
                    "start_date": request.GET.get("start_date", ""),
                    "end_date": request.GET.get("end_date", ""),
                    "error": (
                        "Een of meer activiteiten bevatten ongeldige gegevens."
                    ),
                },
            )

        formset = ActiviteitenFormSet(initial=initial_data)
        self._disable_date_fields(formset)

        return render(
            request,
            self.template_name,
            {
                "formset": formset,
                "start_date": request.GET.get("start_date", ""),
                "end_date": request.GET.get("end_date", ""),
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        formset = ActiviteitenFormSet(request.POST)

        if not formset.is_valid():
            logger.warning(
                "Ongeldige ActiviteitenFormSet: %s",
                formset.errors,
            )

            self._disable_date_fields(formset)

            return render(
                request,
                self.template_name,
                {
                    "formset": formset,
                    "start_date": request.GET.get("start_date", ""),
                    "end_date": request.GET.get("end_date", ""),
                },
            )

        for form in formset.forms:
            if form.cleaned_data.get("importeren"):
                form.save()

        return redirect(self._get_success_url(request))

    def _get_events(self, client: WeeztixClient) -> list[dict[str, Any]]:
        response = client.get("/event")

        if not isinstance(response, list):
            raise WeeztixAPIError(
                "Weeztix heeft geen geldige eventlijst teruggegeven."
            )

        return [
            event
            for event in response
            if isinstance(event, dict)
        ]

    def _exclude_imported_events(
        self,
        events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        imported_guids = set(
            Activiteit.objects.exclude(guid__isnull=True)
            .exclude(guid="")
            .values_list("guid", flat=True)
        )

        return [
            event
            for event in events
            if event.get("guid")
            and event.get("guid") not in imported_guids
        ]

    def _filter_events_by_date(
        self,
        events: list[dict[str, Any]],
        start_date: date | None,
        end_date: date | None,
    ) -> list[dict[str, Any]]:
        if not start_date and not end_date:
            return events

        filtered_events: list[dict[str, Any]] = []

        for event in events:
            start, _ = self._get_event_dates(event)

            event_date = self._parse_iso_date(start)

            if event_date is None:
                logger.warning(
                    "Weeztix-event %s overgeslagen: geen geldige startdatum.",
                    event.get("guid"),
                )
                continue

            if start_date and event_date < start_date:
                continue

            if end_date and event_date > end_date:
                continue

            filtered_events.append(event)

        return filtered_events

    def _build_initial_data(self, client: WeeztixClient, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        initial_data: list[dict[str, Any]] = []
        processed_guids: set[str] = set()

        fallback_place = Plaats.objects.filter(naam="Overig").first()

        if fallback_place is None:
                logger.warning('Fallbackplaats "Overig" bestaat niet.')

        for event in events:
            guid = event.get("guid")

            if not guid or guid in processed_guids:
                continue

            start, end = self._get_event_dates(event)

            begin_date = self._parse_iso_date(start)

            if begin_date is None:
                logger.warning(
                    "Weeztix-event %s overgeslagen: geen geldige startdatum.",
                    guid,
                )
                continue

            end_date = self._parse_iso_date(end) or begin_date

            try:
                shops = self._get_event_shops(client=client, guid=guid)
                amount = self._get_event_max_price(client=client, guid=guid)

            except WeeztixAPIError:
                logger.exception(
                    "Aanvullende gegevens voor Weeztix-event %s "
                    "konden niet worden opgehaald.",
                    guid,
                )
                continue

            shop_name, place = self._resolve_place(
                shops=shops,
                fallback_place=fallback_place,
            )

            if place is None:
                logger.warning(
                    "Weeztix-event %s overgeslagen: geen plaats gevonden "
                    'en fallbackplaats "Overig" bestaat niet.',
                    guid,
                )
                continue

            initial_data.append(
                {
                    "guid": guid,
                    "naam": event.get("name", ""),
                    "shop": shop_name,
                    "plaats": place,
                    "datum": begin_date,
                    "begin_datum": begin_date,
                    "eind_datum": end_date,
                    "bedrag": amount,
                }
            )

            processed_guids.add(guid)

        initial_data.sort(
            key=lambda item: item["begin_datum"]
        )

        return initial_data

    def _get_event_shops(
        self,
        client: WeeztixClient,
        guid: str,
    ) -> list[dict[str, Any]]:
        response = client.get(f"/event/{guid}/shops")

        if not isinstance(response, list):
            raise WeeztixAPIError(
                f"Weeztix heeft geen geldige shoplijst "
                f"voor event {guid} teruggegeven."
            )

        return [
            shop
            for shop in response
            if isinstance(shop, dict)
        ]

    def _get_event_max_price(
        self,
        client: WeeztixClient,
        guid: str,
    ) -> Decimal:
        response = client.get(f"/event/{guid}/ticket")

        if not isinstance(response, list):
            raise WeeztixAPIError(
                f"Weeztix heeft geen geldige ticketlijst "
                f"voor event {guid} teruggegeven."
            )

        maximum_price = Decimal("0.00")

        for ticket_type in response:
            if not isinstance(ticket_type, dict):
                continue

            minimum_price = ticket_type.get("min_price", 0)

            try:
                price_in_cents = Decimal(str(minimum_price or 0))
            except InvalidOperation:
                logger.warning(
                    "Ongeldige ticketprijs voor event %s: %r",
                    guid,
                    minimum_price,
                )
                continue

            price_in_euros = (
                price_in_cents / Decimal("100")
            ).quantize(Decimal("0.01"))

            maximum_price = max(
                maximum_price,
                price_in_euros,
            )

        return maximum_price

    @staticmethod
    def _get_event_dates(
        event: dict[str, Any],
    ) -> tuple[str | None, str | None]:
        start = event.get("start")
        end = event.get("end")

        if start:
            return start, end

        event_dates = event.get("event_dates") or []

        if not isinstance(event_dates, list):
            return None, None

        if not event_dates:
            return None, None

        first_event_date = event_dates[0]

        if not isinstance(first_event_date, dict):
            return None, None

        return (
            first_event_date.get("start"),
            first_event_date.get("end"),
        )

    @staticmethod
    def _parse_iso_date(value: Any) -> date | None:
        if not value or not isinstance(value, str):
            return None

        normalized_value = value.strip()

        if normalized_value.endswith("Z"):
            normalized_value = (
                f"{normalized_value[:-1]}+00:00"
            )

        try:
            return datetime.fromisoformat(
                normalized_value
            ).date()
        except ValueError:
            return None

    @staticmethod
    def _resolve_place(
        shops: list[dict[str, Any]],
        fallback_place: Plaats | None,
    ) -> tuple[str, Plaats | None]:
        for shop in shops:
            shop_name = str(
                shop.get("name") or ""
            ).strip()

            if not shop_name:
                continue

            place = Plaats.objects.filter(
                shop_naam=shop_name
            ).first()

            if place is not None:
                return shop_name, place

        if shops:
            first_shop_name = str(
                shops[0].get("name") or ""
            ).strip()

            return first_shop_name, fallback_place

        return "", fallback_place

    @staticmethod
    def _disable_date_fields(
        formset: ActiviteitenFormSet,
    ) -> None:
        for form in formset.forms:
            if "datum" in form.fields:
                form.fields["datum"].disabled = True

    @staticmethod
    def _get_success_url(
        request: HttpRequest,
    ) -> str:
        start_date, end_date = parse_dutch_date_range(
            request.GET.get("start_date"),
            request.GET.get("end_date"),
        )

        query_parameters: dict[str, str] = {}

        if start_date:
            query_parameters["start_date"] = (
                format_dutch_date(start_date)
            )

        if end_date:
            query_parameters["end_date"] = (
                format_dutch_date(end_date)
            )

        url = reverse("core:ticket_update")

        if query_parameters:
            url = (
                f"{url}?"
                f"{urlencode(query_parameters)}"
            )

        return url

@method_decorator(is_begeleider_required, name='dispatch')
class ActiviteitDetailView(DetailView):

    model = Activiteit
    template_name = "core/activiteit/activiteit_detail.html"
    context_object_name = "activiteit"

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Haal de activiteit op
        activiteit = self.get_object()

        tickets = Ticket.objects.filter(activiteit=activiteit).exclude(deelnemer__naam="NOG IN TE DELEN").order_by('gekocht_op')

        context['gekochte_tickets'] = tickets
        context['aantal_tickets'] = len(tickets)
        return context

@method_decorator(is_begeleider_required, name='dispatch')
class ActiviteitUpdateView(UpdateView):

    model = Activiteit
    template_name = "core/activiteit/activiteit_update.html"
    context_object_name = "activiteit"

    fields = ["naam", 'begin_datum', "eind_datum", "plaats", "type_activiteit", "bedrag"]

@method_decorator(is_begeleider_required, name='dispatch')
class ActiviteitDeleteView(DeleteView):
    model = Activiteit
    template_name = 'core/activiteit/activiteit_delete.html'
    success_url = reverse_lazy('core:activiteit_list')