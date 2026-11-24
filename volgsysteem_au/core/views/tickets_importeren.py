from datetime import date, datetime, time
from io import BytesIO
from typing import Any
import pandas as pd
import requests
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import ListView, View
from core.forms import TicketAddFormSet
from core.models import Activiteit, Deelnemer, DeelnemerVolgsysteem, Plaats, Ticket, WoonPlaatsDeelnemer
from core.permissions import is_begeleider_required
from core.services.volgsysteem import verwijder_acties_voor_deelnemers
from core.services.weeztix.exports import WeeztixExportService
from core.services.weeztix.exceptions import WeeztixError, WeeztixExportNotReady
from core.utils.dates import parse_dutch_date_range

def set_capitals_name(naam: str) -> str:
    """Normaliseer een ticketnaam en verwijder een afsluitende aanduiding DB."""
    naam = naam.strip()

    if naam.endswith("DB"):
        naam = " ".join(naam.split()[:-1])

    naamdelen = naam.split()
    if not naamdelen:
        return ""

    if len(naamdelen) <= 2:
        return naam.title()

    voornaam, *tussenvoegsels, achternaam = naamdelen
    tussenvoegsels_tekst = " ".join(
        tussenvoegsel.lower() for tussenvoegsel in tussenvoegsels
    )
    return f"{voornaam.title()} {tussenvoegsels_tekst} {achternaam.title()}"


# Tijdelijk behouden voor bestaande imports of aanroepen.
SetCapitalsName = set_capitals_name


@method_decorator(is_begeleider_required, name="dispatch")
class DownloadTicketReport(View):
    template_name = "core/ticket/tickets_to_add_list.html"

    @staticmethod
    def get_in_te_delen_deelnemer():
        return Deelnemer.objects.filter(naam="NOG IN TE DELEN").first()

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        formset1 = TicketAddFormSet(request.POST, prefix="form1")
        formset2 = TicketAddFormSet(request.POST, prefix="form2")
        alles_correct = True

        for formset in (formset1, formset2):
            if not formset.is_valid():
                alles_correct = False
                continue

            geldige_formulieren = [
                form
                for form in formset.forms
                if form.cleaned_data.get("importeren")
            ]
            deelnemers_updaten = [
                form.cleaned_data.get("deelnemer")
                for form in geldige_formulieren
                if form.cleaned_data.get("deelnemer") is not None
            ]

            verwijder_acties_voor_deelnemers(deelnemers_updaten)
            DeelnemerVolgsysteem.objects.filter(
                deelnemer__in=deelnemers_updaten,
            ).update(
                deelnemer_actie1=None,
                deelnemer_actie2=None,
                deelnemer_actie3=None,
            )

            for form in geldige_formulieren:
                deelnemer = form.cleaned_data.get("deelnemer")
                ongeldige_deelnemer = deelnemer is None
                externe_deelnemer = (
                    deelnemer is not None and deelnemer.naam == "EXTERN"
                )

                if ongeldige_deelnemer or externe_deelnemer:
                    form.cleaned_data["deelnemer"] = None
                    woonplaats = WoonPlaatsDeelnemer.objects.get(
                        naam="ONBEKEND"
                    )
                else:
                    woonplaats_deelnemer = deelnemer.woonplaats
                    if woonplaats_deelnemer in {
                        "Denbosch",
                        "'S-Hertogenbosch",
                        "S-hertogenbosch",
                        "s-Hertogenbosch",
                        "'s-Hertogenbosch",
                    }:
                        woonplaats_deelnemer = "Den Bosch"

                    try:
                        woonplaats = WoonPlaatsDeelnemer.objects.get(
                            naam=woonplaats_deelnemer
                        )
                    except WoonPlaatsDeelnemer.DoesNotExist:
                        woonplaats = WoonPlaatsDeelnemer.objects.get(
                            naam="ONBEKEND"
                        )

                form.cleaned_data["woonplaats_deelnemer"] = woonplaats
                form.save()

        if alles_correct:
            self._clear_report_session(request)
            return redirect("core:ticket_list")

        return render(
            request,
            self.template_name,
            {
                "formset": formset1,
                "formset_overig": formset2,
            },
        )

    def get(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        deelnemer_nog_in_te_delen = self.get_in_te_delen_deelnemer()
        if deelnemer_nog_in_te_delen is None:
            messages.error(
                request,
                'De systeemdeelnemer "NOG IN TE DELEN" ontbreekt. '
                "Maak dit record eerst aan voordat tickets worden geïmporteerd.",
            )
            return redirect("core:ticket_list")

        guid = request.session.get("report_guid")
        activiteiten = request.session.get("activiteiten")
        if not guid:
            messages.error(request, "Er is geen Weeztix-rapport beschikbaar.")
            return redirect("core:ticket_list")

        hash_values = self._get_bestaande_hash_values(activiteiten)

        print("REPORT GUID:", guid)
        print("ACTIVITEITEN:", activiteiten)
        print("AANTAL BESTAANDE HASH VALUES:", len(hash_values))

        export_service = WeeztixExportService(user=request.user)

        try:
            print("START DOWNLOAD XLSX")

            xlsx_content = export_service.download_xlsx(guid)

            print("DOWNLOAD KLAAR")
            print("XLSX BYTES:", len(xlsx_content))

            ticket_data = pd.read_excel(
                BytesIO(xlsx_content),
                engine="openpyxl",
            )

            print("EXCEL GELEZEN")
            print("AANTAL EXCEL RIJEN:", len(ticket_data))
            print("EXCEL KOLOMMEN:", ticket_data.columns.tolist())

        except WeeztixExportNotReady:
            print("EXPORT NOG NIET KLAAR")

            return self._render_import_page(
                request,
                error_msg=(
                    "Het Weeztix-rapport is nog niet gereed. "
                    "Probeer het over enkele seconden opnieuw."
                ),
            )

        except WeeztixError as error:
            print("WEEZTIX ERROR:", repr(error))

            return self._render_import_page(
                request,
                error_msg=f"Fout bij ophalen van de Weeztix-export: {error}.",
            )

        except (ImportError, OSError, ValueError, KeyError) as error:
            print("EXCEL ERROR:", repr(error))

            return self._render_import_page(
                request,
                error_msg=f"Het Weeztix Excel-bestand kon niet worden gelezen: {error}.",
            )

        # Opruimen is best effort. Een mislukte DELETE mag een reeds
        # gedownloade en leesbare ticketexport niet blokkeren.
        try:
            export_service.delete(guid)
        except WeeztixError:
            pass

        vereiste_kolommen = {
            "ticket_invalidated",
            "first_name",
            "last_name",
            "barcode",
            "shop_name",
            "first_event_date_start",
            "last_event_date_end",
            "event_name",
            "created_at",
            "ticket_value",
        }
        ontbrekende_kolommen = vereiste_kolommen.difference(ticket_data.columns)
        if ontbrekende_kolommen:
            return self._render_import_page(
                request,
                error_msg=(
                    "Het Weeztix-bestand mist vereiste kolommen: "
                    + ", ".join(sorted(ontbrekende_kolommen))
                    + "."
                ),
            )

        ticket_data = ticket_data[ticket_data["ticket_invalidated"].isna()]
        print("AANTAL GELDIGE TICKETS NA INVALIDATED FILTER:", len(ticket_data))
        alle_plaatsen = list(Plaats.objects.all())
        plaats_overig = next(
            (plaats for plaats in alle_plaatsen if plaats.naam == "Overig"),
            None,
        )

        excel_namen = self._get_excel_namen(ticket_data)
        deelnemers_dict = {
            deelnemer.naam_tickets: deelnemer
            for deelnemer in Deelnemer.objects.filter(
                naam_tickets__in=excel_namen
            )
        }

        payloads_aanpassen: list[dict[str, Any]] = []
        payloads_niet_aanpassen: list[dict[str, Any]] = []

        for _, rij in ticket_data.iterrows():
            payload = self._maak_ticket_payload(
                rij=rij,
                hash_values=hash_values,
                geselecteerde_activiteiten=activiteiten,
                alle_plaatsen=alle_plaatsen,
                plaats_overig=plaats_overig,
                deelnemers_dict=deelnemers_dict,
                deelnemer_nog_in_te_delen=deelnemer_nog_in_te_delen,
            )
            if payload is None:
                continue

            if payload["deelnemer"].pk == deelnemer_nog_in_te_delen.pk:
                payloads_aanpassen.append(payload)
            else:
                payloads_niet_aanpassen.append(payload)

        if not (payloads_aanpassen or payloads_niet_aanpassen):
            self._clear_report_session(request)
            return render(
                request,
                self.template_name,
                {"geen_tickets": True},
            )

        payloads_aanpassen = self._sort_payloads(payloads_aanpassen)
        payloads_niet_aanpassen = self._sort_payloads(
            payloads_niet_aanpassen
        )

        formset1 = TicketAddFormSet(
            initial=payloads_aanpassen,
            prefix="form1",
        )
        formset2 = TicketAddFormSet(
            initial=payloads_niet_aanpassen,
            prefix="form2",
        )

        self._set_readonly_fields(
            formset1,
            (
                "bedrag",
                "deelnemer_naam_ticket",
                "activiteit_datum",
                "activiteit_naam",
            ),
        )
        self._set_readonly_fields(
            formset2,
            (
                "bedrag",
                "deelnemer_naam",
                "activiteit_datum",
                "deelnemer_naam_ticket",
                "activiteit_naam",
            ),
        )

        return render(
            request,
            self.template_name,
            {
                "formset": formset1,
                "formset_overig": formset2,
            },
        )

    def _maak_ticket_payload(
        self,
        *,
        rij: pd.Series,
        hash_values: set,
        geselecteerde_activiteiten: list[str],
        alle_plaatsen: list[Plaats],
        plaats_overig: Plaats | None,
        deelnemers_dict: dict[str, Deelnemer],
        deelnemer_nog_in_te_delen: Deelnemer,
    ) -> dict[str, Any] | None:
        hash_value = rij.get("barcode")
        print("\n--- TICKETRIJ VERWERKEN ---")
        print("BARCODE:", rij.get("barcode"))
        print("EVENT:", rij.get("event_name"))
        print("BEGIN:", rij.get("first_event_date_start"))
        print("EIND:", rij.get("last_event_date_end"))
        if pd.isna(hash_value):
            print("OVERGESLAGEN: barcode ontbreekt")
            return None

        if hash_value in hash_values:
            print("OVERGESLAGEN: barcode bestaat al:", hash_value)
            return None

        shop = rij.get("shop_name")
        plaats = next(
            (
                plaats_item
                for plaats_item in alle_plaatsen
                if plaats_item.shop_naam == shop
            ),
            plaats_overig,
        )

        begin_datum_waarde = rij.get("first_event_date_start")
        eind_datum_waarde = rij.get("last_event_date_end")
        if pd.isna(begin_datum_waarde) or pd.isna(eind_datum_waarde):
            return None

        try:
            begin_datum = self._parse_api_datetime(begin_datum_waarde)
            eind_datum = self._parse_api_datetime(eind_datum_waarde)
            gekocht_op = self._parse_api_datetime(rij.get("created_at"))
        except (TypeError, ValueError):
            return None

        event_naam = str(rij.get("event_name") or "").strip()

        print(
            "TICKET KOPPELEN:",
            {
                "event_naam": event_naam,
                "begin_datum": begin_datum,
                "eind_datum": eind_datum,
                "shop": shop,
                "plaats": plaats,
            },
        )

        activiteiten_queryset = Activiteit.objects.filter(
            guid__in=geselecteerde_activiteiten,
            naam__iexact=str(event_naam).strip(),
        )

        print(
            "GEVONDEN ACTIVITEITEN:",
            list(
                activiteiten_queryset.values(
                    "id",
                    "naam",
                    "begin_datum",
                    "eind_datum",
                    "plaats_id",
                )
            ),
        )

        activiteit = activiteiten_queryset.filter(plaats=plaats).first()

        if activiteit is None:
            if activiteiten_queryset.count() != 1:
                print(
                    "TICKET OVERGESLAGEN: activiteit niet eenduidig gevonden",
                    {
                        "event_naam": event_naam,
                        "begin_datum": begin_datum,
                        "eind_datum": eind_datum,
                    },
                )
                return None
            activiteit = activiteiten_queryset.first()

        voornaam = rij.get("first_name")
        achternaam = rij.get("last_name")
        if pd.isna(voornaam) or pd.isna(achternaam):
            return None

        deelnemer_naam_ticket = set_capitals_name(
            f"{str(voornaam).strip()} {str(achternaam).strip()}"
        )
        deelnemer = deelnemers_dict.get(
            deelnemer_naam_ticket,
            deelnemer_nog_in_te_delen,
        )

        try:
            bedrag_ticket = float(rij.get("ticket_value", 0) or 0)
        except (TypeError, ValueError):
            return None

        bedrag_activiteit = activiteit.bedrag if activiteit else 0
        if bedrag_activiteit == 0:
            type_ticket = 2
        elif bedrag_activiteit == bedrag_ticket:
            type_ticket = 0
        elif bedrag_ticket == 0:
            type_ticket = 1
        else:
            type_ticket = 3

        return {
            "activiteit": activiteit,
            "activiteit_naam": activiteit.naam if activiteit else "",
            "activiteit_datum": activiteit.begin_datum,
            "deelnemer_naam_ticket": deelnemer_naam_ticket,
            "deelnemer": deelnemer,
            "gekocht_op": gekocht_op,
            "bedrag": bedrag_ticket,
            "type_ticket": type_ticket,
            "hash_value": hash_value,
            "deelnemer_naam": deelnemer.naam,
        }

    @staticmethod
    def _get_excel_namen(ticket_data: pd.DataFrame) -> set[str]:
        excel_namen: set[str] = set()
        for _, rij in ticket_data.iterrows():
            voornaam = rij.get("first_name")
            achternaam = rij.get("last_name")
            if pd.isna(voornaam) or pd.isna(achternaam):
                continue

            excel_namen.add(
                set_capitals_name(
                    f"{str(voornaam).strip()} {str(achternaam).strip()}"
                )
            )
        return excel_namen

    @staticmethod
    def _get_bestaande_hash_values(activiteiten) -> set:
        queryset = Ticket.objects.all()
        if activiteiten:
            queryset = queryset.filter(activiteit__guid__in=activiteiten)
        return set(queryset.values_list("hash_value", flat=True))

    @staticmethod
    def _clear_report_session(request: HttpRequest) -> None:
        request.session.pop("report_guid", None)
        request.session.pop("activiteiten", None)

    def _render_import_page(
        self,
        request: HttpRequest,
        *,
        error_msg: str,
    ) -> HttpResponse:
        return render(
            request,
            self.template_name,
            {
                "formset": TicketAddFormSet(prefix="form1"),
                "formset_overig": TicketAddFormSet(prefix="form2"),
                "error_msg": error_msg,
            },
        )

    @staticmethod
    def _parse_api_datetime(value: Any) -> datetime:
        """Parse een ISO-datum uit Weeztix of een pandas/Excel-datum."""
        if value is None or pd.isna(value):
            raise ValueError("Lege datumwaarde")

        if isinstance(value, pd.Timestamp):
            parsed_value = value.to_pydatetime()
        elif isinstance(value, datetime):
            parsed_value = value
        else:
            parsed_value = datetime.fromisoformat(str(value))

        if timezone.is_naive(parsed_value):
            return timezone.make_aware(parsed_value)
        return parsed_value

    @staticmethod
    def _sort_payloads(
        payloads: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return sorted(
            payloads,
            key=lambda payload: (
                payload.get("activiteit_datum") or date.max,
                str(payload.get("deelnemer") or ""),
            ),
        )

    @staticmethod
    def _set_readonly_fields(
        formset,
        field_names: tuple[str, ...],
    ) -> None:
        for form in formset:
            for field_name in field_names:
                field = form.fields.get(field_name)
                if field is not None:
                    field.widget.attrs["readonly"] = True


@method_decorator(is_begeleider_required, name="dispatch")
class SelectActiviteitenVoorTicketsView(ListView):
    template_name = (
        "core/activiteit/activiteit_list_new_tickets.html"
    )
    model = Activiteit
    ordering = ["-datum"]

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        geselecteerde_activiteiten = request.POST.getlist(
            "geselecteerde_activiteiten"
        )
        if not geselecteerde_activiteiten:
            messages.warning(request, "Selecteer minimaal één activiteit.")
            return redirect("core:ticket_list")

        export_service = WeeztixExportService(user=request.user)

        try:
            export = export_service.start(
                event_ids=geselecteerde_activiteiten,
                name="Ticketexport Avondje Uit",
                description="Ticketexport voor Avondje Uit",
            )
        except WeeztixError as error:
            messages.error(
                request,
                f"De ticketexport kon niet worden gestart: {error}.",
            )
            return redirect("core:ticket_list")

        guid = export.guid

        request.session["activiteiten"] = geselecteerde_activiteiten
        request.session["report_guid"] = guid
        return redirect("core:tickets_loading")

    def get(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        try:
            start_date, end_date = parse_dutch_date_range(
                request.GET.get("start_date"),
                request.GET.get("end_date"),
            )
        except ValueError:
            messages.error(
                request,
                "Gebruik geldige datums in het formaat dd-mm-jjjj. "
                "De einddatum mag niet vóór de startdatum liggen.",
            )
            return redirect("core:ticket_list")

        if start_date is None:
            start_date = date(2025, 1, 1)
        if end_date is None:
            end_date = timezone.localdate()

        start_datetime = timezone.make_aware(
            datetime.combine(start_date, time.min)
        )
        end_datetime = timezone.make_aware(
            datetime.combine(end_date, time.max)
        )

        activiteiten = (
            Activiteit.objects.filter(
                begin_datum__gte=start_datetime,
                eind_datum__lte=end_datetime,
            )
            .select_related("plaats")
            .order_by("begin_datum")
        )

        return render(
            request,
            self.template_name,
            {"activiteiten": activiteiten},
        )