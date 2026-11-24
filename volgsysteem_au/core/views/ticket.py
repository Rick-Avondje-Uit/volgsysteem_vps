import logging
from typing import Any
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DeleteView, ListView, UpdateView
from core.forms import TicketAddFormSet, TicketFilterForm, TicketToewijzenFormSet
from core.models import Ticket
from core.permissions import is_begeleider_required
from core.services.volgsysteem import verwijder_acties_voor_deelnemers
from core.services.weeztix.client import WeeztixClient
from core.services.weeztix.exceptions import WeeztixAPIError


logger = logging.getLogger(__name__)


@method_decorator(
    is_begeleider_required,
    name="dispatch",
)
class CheckReportStatus(View):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        report_guid = request.session.get("report_guid")

        if not report_guid:
            return JsonResponse(
                {
                    "finished": False,
                    "error": "Er is geen Weeztix-export gestart.",
                },
                status=400,
            )

        # Eén client voor dit volledige Django-request.
        client = WeeztixClient.from_user(request.user)

        try:
            response = client.get(
                f"/export/{report_guid}"
            )

        except WeeztixAPIError:
            logger.exception(
                "Status van Weeztix-export %s kon niet "
                "worden opgehaald.",
                report_guid,
            )

            return JsonResponse(
                {
                    "finished": False,
                    "error": (
                        "De status van de Weeztix-export kon "
                        "niet worden opgehaald."
                    ),
                },
                status=502,
            )

        if not isinstance(response, dict):
            logger.warning(
                "Ongeldige statusresponse voor "
                "Weeztix-export %s: %r",
                report_guid,
                response,
            )

            return JsonResponse(
                {
                    "finished": False,
                    "error": (
                        "Weeztix gaf geen geldige exportstatus terug."
                    ),
                },
                status=502,
            )

        download_links = response.get("download_links") or {}

        if not isinstance(download_links, dict):
            logger.warning(
                "Ongeldige download_links voor "
                "Weeztix-export %s: %r",
                report_guid,
                download_links,
            )

            return JsonResponse(
                {
                    "finished": False,
                    "error": (
                        "Weeztix gaf geen geldige downloadinformatie "
                        "terug."
                    ),
                },
                status=502,
            )

        download_link = download_links.get("xlsx")

        return JsonResponse(
            {
                "finished": bool(download_link),
            }
        )


@method_decorator(is_begeleider_required, name="dispatch")
class TicketsLoading(View):
    template_name = "core/ticket/tickets_loading.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return render(
            request,
            self.template_name,
        )


@method_decorator(is_begeleider_required, name="dispatch",)
class TicketListView(ListView):
    template_name = "core/ticket/ticket_list.html"
    model = Ticket
    context_object_name = "tickets"
    paginate_by = 50

    def get_queryset(self):
        queryset = (
            Ticket.objects
            .select_related(
                "deelnemer",
                "activiteit",
                "activiteit__plaats",
            )
            .order_by("-gekocht_op")
        )

        self.filter_form = TicketFilterForm(
            self.request.GET
        )

        if not self.filter_form.is_valid():
            return queryset

        deelnemer = self.filter_form.cleaned_data.get(
            "deelnemer_keuze"
        )
        plaats = self.filter_form.cleaned_data.get(
            "plaats_keuze"
        )
        datum_start = self.filter_form.cleaned_data.get(
            "datum_start"
        )
        datum_end = self.filter_form.cleaned_data.get(
            "datum_end"
        )

        if deelnemer:
            queryset = queryset.filter(
                deelnemer_id=self._get_object_id(deelnemer)
            )

        if plaats:
            queryset = queryset.filter(
                activiteit__plaats_id=self._get_object_id(
                    plaats
                )
            )

        if datum_start:
            queryset = queryset.filter(
                gekocht_op__date__gte=datum_start
            )

        if datum_end:
            queryset = queryset.filter(
                gekocht_op__date__lte=datum_end
            )

        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["form"] = getattr(
            self,
            "filter_form",
            TicketFilterForm(self.request.GET),
        )

        return context

    @staticmethod
    def _get_object_id(value: Any) -> Any:
        """
        Ondersteunt zowel een ModelChoiceField-resultaat
        als een rechtstreeks numeriek ID.
        """
        return getattr(value, "pk", value)


@method_decorator(is_begeleider_required, name="dispatch",)
class TicketUpdateView(UpdateView):
    template_name = "core/ticket/tickets_update.html"
    model = Ticket
    fields = [
        "activiteit",
        "deelnemer",
        "bedrag",
        "type_ticket",
    ]
    context_object_name = "ticket"

    def get_success_url(self) -> str:
        return reverse(
            "core:activiteit_detail",
            kwargs={
                "pk": self.object.activiteit_id,
            },
        )


@method_decorator(is_begeleider_required, name="dispatch",)
class TicketDeleteView(DeleteView):
    model = Ticket
    template_name = "core/ticket/ticket_delete.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["activiteit_id"] = (
            self.object.activiteit_id
        )

        return context

    def get_success_url(self) -> str:
        return reverse(
            "core:activiteit_detail",
            kwargs={
                "pk": self.object.activiteit_id,
            },
        )


@method_decorator(is_begeleider_required, name="dispatch")


class TicketsNogToeTeWijzenListView(View):
    template_name = (
        "core/ticket/tickets_toewijzen_list.html"
    )
    formset_prefix = "form1"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        tickets = (
            Ticket.objects
            .filter(
                deelnemer__naam="NOG IN TE DELEN"
            )
            .select_related(
                "activiteit",
                "deelnemer",
            )
            .order_by("-gekocht_op")
        )

        payloads = [
            self._build_ticket_payload(ticket)
            for ticket in tickets
        ]

        if not payloads:
            return render(
                request,
                self.template_name,
                {
                    "geen_tickets": True,
                },
            )

        formset = TicketToewijzenFormSet(
            initial=payloads,
            prefix=self.formset_prefix,
        )

        self._configure_formset_fields(formset)

        return render(
            request,
            self.template_name,
            {
                "formset": formset,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:

        formset = TicketToewijzenFormSet(
            request.POST,
            prefix=self.formset_prefix,
        )

        valid = formset.is_valid()

        if not valid:

            self._configure_formset_fields(formset)

            return render(
                request,
                self.template_name,
                {
                    "formset": formset,
                },
            )

        selected_forms = []

        for index, form in enumerate(formset.forms):
            if form.cleaned_data.get("importeren"):
                selected_forms.append(form)

        if not selected_forms:
            formset._non_form_errors = formset.error_class(["Selecteer minimaal één ticket om toe te wijzen."])
            self._configure_formset_fields(formset)

            return render(
                request,
                self.template_name,
                {
                    "formset": formset,
                },
            )

        with transaction.atomic():
            tickets_by_id = self._get_tickets_by_id(
                selected_forms
            )

            missing_tickets = self._add_missing_ticket_errors(
                forms=selected_forms,
                tickets_by_id=tickets_by_id,
            )

            if not missing_tickets:
                deelnemers = self._get_selected_participants(
                    selected_forms
                )

                if deelnemers:
                    verwijder_acties_voor_deelnemers(
                        deelnemers
                    )

                self._assign_tickets(
                    forms=selected_forms,
                    tickets_by_id=tickets_by_id,
                )

        if missing_tickets:
            self._configure_formset_fields(formset)
            return render(request, self.template_name, {"formset": formset,})

        return redirect("core:ticket_list")

    @staticmethod
    def _build_ticket_payload(ticket: Ticket) -> dict[str, Any]:
        activiteit = ticket.activiteit

        activiteit_datum = getattr(
            activiteit,
            "begin_datum",
            None,
        )

        if activiteit_datum is None:
            activiteit_datum = getattr(
                activiteit,
                "datum",
                None,
            )

        return {
            "ticket_id": ticket.pk,
            "activiteit_naam": activiteit.naam,
            "activiteit_datum": activiteit_datum,
            "deelnemer_naam_ticket": ticket.deelnemer_naam_ticket,
            "deelnemer": None
        }

    @staticmethod
    def _configure_formset_fields(
        formset: TicketAddFormSet,
    ) -> None:
        readonly_fields = (
            "deelnemer_naam_ticket",
            "activiteit_datum",
            "activiteit_naam",
        )

        for form in formset.forms:
            for field_name in readonly_fields:
                if field_name in form.fields:
                    form.fields[
                        field_name
                    ].widget.attrs["readonly"] = True

    @staticmethod
    def _get_tickets_by_id(
            forms: list[Any],
    ) -> dict[int, Ticket]:
        ticket_ids = {
            form.cleaned_data.get("ticket_id")
            for form in forms
            if form.cleaned_data.get("ticket_id")
        }

        tickets = (
            Ticket.objects
            .select_for_update()
            .filter(pk__in=ticket_ids)
        )

        return {
            ticket.pk: ticket
            for ticket in tickets
        }

    @staticmethod
    def _add_missing_ticket_errors(
        *,
        forms: list[Any],
        tickets_by_id: dict[int, Ticket],
    ) -> bool:
        missing_ticket_found = False

        for form in forms:
            ticket_id = form.cleaned_data.get(
                "ticket_id",
            )

            if (
                not ticket_id
                or ticket_id not in tickets_by_id
            ):
                form.add_error(
                    "ticket_id",
                    (
                        "Het bijbehorende ticket bestaat niet "
                        "meer. Vernieuw de pagina en probeer "
                        "het opnieuw."
                    ),
                )
                missing_ticket_found = True

        return missing_ticket_found

    @staticmethod
    def _get_selected_participants(
        forms: list[Any],
    ) -> list[Any]:
        deelnemers = []

        for form in forms:
            deelnemer = form.cleaned_data.get(
                "deelnemer"
            )

            if deelnemer is None:
                continue

            # EXTERN wordt uiteindelijk als None opgeslagen.
            # Hiervoor hoeven geen deelnemersacties te worden
            # verwijderd.
            if deelnemer.naam == "EXTERN":
                continue

            deelnemers.append(deelnemer)

        return deelnemers

    @staticmethod
    def _assign_tickets(
        *,
        forms: list[Any],
        tickets_by_id: dict[int, Ticket],
    ) -> None:
        tickets_to_update: list[Ticket] = []

        for form in forms:
            ticket_id = form.cleaned_data[
                "ticket_id"
            ]
            ticket = tickets_by_id[ticket_id]

            deelnemer = form.cleaned_data.get(
                "deelnemer"
            )

            if (
                deelnemer is not None
                and deelnemer.naam == "EXTERN"
            ):
                deelnemer = None
            ticket.deelnemer = deelnemer
            tickets_to_update.append(ticket)

        Ticket.objects.bulk_update(
            tickets_to_update,
            fields=["deelnemer"],
        )