from datetime import datetime, timedelta
import phonenumbers
from django import forms
from django.forms import formset_factory
from .models import Activiteit, Begeleider, DagRapportage, Deelnemer, DeelnemerInstroom, DeelnemerUitstroom, DeelnemerVolgsysteem, HoofdDoel, MethodiekPunten, Plaats, RapportageDoel, SubDoel, Ticket, VolgsysteemInstelling
from core.utils.dates import DUTCH_DATE_FORMAT


class BootstrapFormMixin:
    """Voegt Bootstrap 5-classes toe aan formulierwidgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            widget = field.widget

            if isinstance(widget, forms.HiddenInput):
                continue

            if isinstance(widget, forms.CheckboxInput):
                self._add_widget_class(widget, "form-check-input",)
                continue

            if isinstance(widget, forms.RadioSelect):
                self._add_widget_class(widget, "form-check-input")
                continue

            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                self._add_widget_class(widget,"form-select",)
                continue

            self._add_widget_class(widget,"form-control",)

    @staticmethod
    def _add_widget_class(widget, class_name):
        current_classes = widget.attrs.get("class", "").split()

        if class_name not in current_classes:
            current_classes.append(class_name)

        widget.attrs["class"] = " ".join(current_classes)


class EmptyStringDefaultChoiceWidget(forms.Select):
    def create_option(self, *args, **kwargs):
        option = super().create_option(*args, **kwargs)
        option["empty_value"] = ""
        return option


class DutchPhoneNumberMixin:
    """Normaliseert Nederlandse telefoonnummers naar E.164."""

    def clean_mobiele_nummer(self):
        mobile_number = self.cleaned_data.get("mobiele_nummer")

        if not mobile_number:
            return None

        try:
            parsed_number = phonenumbers.parse(mobile_number, "NL")

        except phonenumbers.NumberParseException as error:
            raise forms.ValidationError(
                "Voer een geldig mobiel nummer in."
            ) from error

        if not phonenumbers.is_valid_number(parsed_number):
            raise forms.ValidationError(
                "Voer een geldig mobiel nummer in."
            )

        return phonenumbers.format_number(parsed_number,phonenumbers.PhoneNumberFormat.E164)

class DeelnemerInstroomUpdateForm(BootstrapFormMixin,forms.ModelForm):
    class Meta:
        model = DeelnemerInstroom
        fields = ("contact_formulier_datum", "intake_datum", "zorgorganisatie_start","heeft_ons_gevonden_via")
        widgets = {"contact_formulier_datum": forms.DateInput(format=DUTCH_DATE_FORMAT, attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"}), "intake_datum": forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"}, format=DUTCH_DATE_FORMAT)}


class DeelnemerUitstroomForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = DeelnemerUitstroom
        fields = ("reden_uitstroming", "wil_op_hoogte_blijven")

class DeelnemerUpdateForm(DutchPhoneNumberMixin, BootstrapFormMixin, forms.ModelForm,):
    class Meta:
        model = Deelnemer
        fields = ("naam", "naam_tickets", "geboortedatum", "woonplaats", "zorgorganisatie", "zorgorganisatie_locatie", "aanmeld_locatie", "mobiele_nummer", "email", "belangrijke_info")
        widgets = {"mobiele_nummer": forms.TextInput(attrs={"placeholder": "+31612345678", "autocomplete": "tel"}), "geboortedatum": forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"}, format=DUTCH_DATE_FORMAT)}


class DeelnemerForm(DutchPhoneNumberMixin, BootstrapFormMixin,forms.ModelForm):
    contact_formulier_datum = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"}, format=DUTCH_DATE_FORMAT))
    intake_datum = forms.DateField(initial=datetime.now().date, widget=forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"}, format=DUTCH_DATE_FORMAT))
    heeft_ons_gevonden_via = forms.CharField(max_length=128, required=False)

    class Meta:
        model = Deelnemer
        fields = (
            "naam",
            "geboortedatum",
            "woonplaats",
            "aanmeld_locatie",
            "mobiele_nummer",
            "email",
            "zorgorganisatie",
            "zorgorganisatie_locatie",
            "belangrijke_info",
        )
        widgets = {"mobiele_nummer": forms.TextInput(attrs={"placeholder": "+31612345678", "autocomplete": "tel"}), "geboortedatum": forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"}, format=DUTCH_DATE_FORMAT)}

    def clean_naam(self):
        naam = self.cleaned_data["naam"]

        if Deelnemer.objects.filter(
            naam__iexact=naam
        ).exists():
            raise forms.ValidationError(
                "Er bestaat al een deelnemer met deze naam."
            )

        return naam

    def save(self, commit=True):
        deelnemer = super().save(commit=False)
        deelnemer.naam_tickets = deelnemer.naam

        if not commit:
            return deelnemer

        deelnemer.save()

        DeelnemerInstroom.objects.create(
            deelnemer=deelnemer,
            contact_formulier_datum=(
                self.cleaned_data[
                    "contact_formulier_datum"
                ]
            ),
            intake_datum=self.cleaned_data[
                "intake_datum"
            ],
            heeft_ons_gevonden_via=(
                self.cleaned_data[
                    "heeft_ons_gevonden_via"
                ]
            ),
            zorgorganisatie_start=(
                self.cleaned_data["zorgorganisatie"]
            ),
        )

        DeelnemerVolgsysteem.objects.create(
            deelnemer=deelnemer,
        )

        return deelnemer


class DeelnemerFilterForm(
    BootstrapFormMixin,
    forms.Form,
):
    actief_keuzes = (
        ("", "Alles"),
        ("true", "Ja"),
        ("false", "Nee"),
    )

    actief = forms.ChoiceField(
        choices=actief_keuzes,
        required=False,
        label="Actief",
    )

    in_methodiek = forms.ChoiceField(
        choices=actief_keuzes,
        required=False,
        label="In methodiek",
    )

    is_uitgestroomd = forms.ChoiceField(
        choices=actief_keuzes,
        required=False,
        label="Is uitgestroomd",
    )


class InstellingenForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = VolgsysteemInstelling
        fields = (
            "tijdsduur",
            "tijdsperiode",
        )


class DeelnemerVolgsysteemForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = DeelnemerVolgsysteem
        fields = (
            "deelnemer_actie1",
            "deelnemer_actie2",
            "deelnemer_actie3",
        )
        widgets = {"deelnemer_actie1": forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"}, format=DUTCH_DATE_FORMAT), "deelnemer_actie2": forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"}, format=DUTCH_DATE_FORMAT), "deelnemer_actie3": forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"}, format=DUTCH_DATE_FORMAT)}


class BegeleiderToevoegenForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = Begeleider
        fields = "__all__"


class MethodiekFilterForm(
    BootstrapFormMixin,
    forms.Form,
):
    begeleider_keuze = forms.ChoiceField(
        choices=(),
        required=False,
        label="Begeleider",
    )

    toon_afgeronde_trajecten = forms.BooleanField(
        initial=False,
        required=False,
        label="Toon afgeronde trajecten",
    )

    toon_gepauzeerde_trajecten = forms.BooleanField(
        initial=False,
        required=False,
        label="Toon gepauzeerde trajecten",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        begeleiders = (
            Begeleider.objects
            .order_by("naam")
            .values_list("id", "naam")
        )

        self.fields["begeleider_keuze"].choices = [
            ("", "Alles"),
            *begeleiders,
        ]


class MethodiekPuntenToevoegenForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = MethodiekPunten
        fields = (
            "deelnemer",
            "begeleider",
            "eerst_volgende_actie",
            "datum_vragenlijst_invullen",
            "begin_gesprek",
        )
        widgets = {"datum_vragenlijst_invullen": forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"}, format=DUTCH_DATE_FORMAT), "begin_gesprek": forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"}, format=DUTCH_DATE_FORMAT)}


class ActiviteitenForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    datum = forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric",}, format=DUTCH_DATE_FORMAT,)

    importeren = forms.BooleanField(
        initial=True,
        required=False,
    )

    class Meta:
        model = Activiteit
        fields = "__all__"


ActiviteitenFormSet = formset_factory(
    ActiviteitenForm,
    extra=0,
)


class HoofdDoelToevoegenForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = HoofdDoel
        fields = (
            "type_doel",
            "tekst",
        )


class SubDoelToevoegenForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = SubDoel
        fields = ("tekst",)


class SubDoelBewerkenForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = SubDoel
        fields = ("tekst", "datum_aangemaakt", "subdoel_afgerond")
        widgets = {"datum_aangemaakt": forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"}, format=DUTCH_DATE_FORMAT)}


class DoelRapportageToevoegenForm(BootstrapFormMixin, forms.ModelForm,):
    class Meta:
        model = RapportageDoel
        fields = ("begeleider", "tekst")


class RapportageToevoegenForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = DagRapportage
        fields = (
            "ingevuld_door",
            "zichtbaar_voor_deelnemer",
            "tekst",
        )


class TicketFilterForm(
    BootstrapFormMixin,
    forms.Form,
):
    deelnemer_keuze = forms.ChoiceField(
        choices=(),
        required=False,
        label="Deelnemer",
    )

    plaats_keuze = forms.ChoiceField(
        choices=(),
        required=False,
        label="Plaats",
    )

    datum_start = forms.DateField(required=False, label="Startdatum", widget=forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"},format=DUTCH_DATE_FORMAT))

    datum_end = forms.DateField(required=False, label="Einddatum", widget=forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"}, format=DUTCH_DATE_FORMAT))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        deelnemers = (
            Deelnemer.objects
            .order_by("naam")
            .values_list("id", "naam")
        )

        plaatsen = (
            Plaats.objects
            .order_by("naam")
            .values_list("id", "naam")
        )

        self.fields["deelnemer_keuze"].choices = [
            ("", "Alles"),
            *deelnemers,
        ]

        self.fields["plaats_keuze"].choices = [
            ("", "Alles"),
            *plaatsen,
        ]


class TicketAddForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    activiteit_naam = forms.CharField(
        max_length=128,
        required=False,
    )

    activiteit_datum = forms.DateField(
        required=False,
    )

    deelnemer_naam = forms.CharField(
        max_length=128,
        required=False,
    )

    importeren = forms.BooleanField(
        initial=True,
        required=False,
    )

    class Meta:
        model = Ticket
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["deelnemer"].queryset = (
            Deelnemer.objects
            .order_by("naam")
        )


TicketAddFormSet = formset_factory(
    TicketAddForm,
    extra=0,
)


class TicketUpdateForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = Ticket
        fields = "__all__"

class TicketToewijzenForm(
    BootstrapFormMixin,
    forms.Form,
):
    ticket_id = forms.IntegerField(
        widget=forms.HiddenInput(),
    )

    activiteit_naam = forms.CharField(
        required=False,
        disabled=True,
    )

    activiteit_datum = forms.DateField(
        required=False,
        disabled=True,
    )

    deelnemer_naam_ticket = forms.CharField(
        required=False,
        disabled=True,
    )

    deelnemer = forms.ModelChoiceField(
        queryset=Deelnemer.objects.exclude(naam="NOG IN TE DELEN").order_by("naam"),
        required=True,
    )

    importeren = forms.BooleanField(
        required=False,
    )

TicketToewijzenFormSet = formset_factory(
    TicketToewijzenForm,
    extra=0,
)


class VolgsysteemListViewForm(
    BootstrapFormMixin,
    forms.Form,
):
    default_date = datetime.now() - timedelta(
        days=30
    )

    date_field = forms.DateField(initial=default_date, required=False, label="Begindatum", widget=forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"}, format=DUTCH_DATE_FORMAT))

    num_dagen_vooruit = forms.IntegerField(
        initial=7,
        required=False,
        label="Toon acties tot zoveel dagen vooruit",
    )


class TicketDownloadForm(
    BootstrapFormMixin,
    forms.Form,
):
    begin_datum = forms.DateField(required=False, label="Begindatum", widget=forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"}, format=DUTCH_DATE_FORMAT))

    eind_datum = forms.DateField(required=False, label="Einddatum", widget=forms.DateInput(attrs={"type": "text", "placeholder": "dd-mm-jjjj", "inputmode": "numeric"}, format=DUTCH_DATE_FORMAT))

    plaats_keuze = forms.MultipleChoiceField(
        choices=(),
        required=True,
        label="Plaats",
    )

    type_activiteit_keuze = (
        forms.MultipleChoiceField(
            choices=(),
            required=True,
            label="Type activiteit",
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        plaatsen = (
            Plaats.objects
            .order_by("naam")
            .values_list("id", "naam")
        )

        activiteittypen = (
            Activiteit.objects
            .order_by("type_activiteit")
            .values_list(
                "type_activiteit",
                flat=True,
            )
            .distinct()
        )

        self.fields["plaats_keuze"].choices = list(
            plaatsen
        )

        self.fields[
            "type_activiteit_keuze"
        ].choices = [
            (type_activiteit, type_activiteit)
            for type_activiteit in activiteittypen
        ]


class UserEmailForm(
    BootstrapFormMixin,
    forms.Form,
):
    email = forms.EmailField(
        label="E-mailadres",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
            },
        ),
    )