from datetime import timedelta
from typing import Any
from django.db.models import Count, Exists, OuterRef, Q, Subquery
from django.db.models.deletion import ProtectedError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from core.forms import (DeelnemerForm, DeelnemerFilterForm, DeelnemerUpdateForm,
                        DeelnemerInstroomUpdateForm, DeelnemerUitstroomForm)
from core.models import Deelnemer, Ticket, DeelnemerInstroom, DeelnemerUitstroom, HoofdDoel, DeelnemerMeedoenRegeling
from core.permissions import is_begeleider_required


@method_decorator(is_begeleider_required, name='dispatch')

class DeelnemerCreateView(CreateView):
    template_name = "core/deelnemer/deelnemer_form.html"
    form_class = DeelnemerForm
    model = Deelnemer

@method_decorator(is_begeleider_required, name='dispatch')

class DeelnemerListView(ListView):
    template_name = "core/deelnemer/deelnemer_list.html"
    model = Deelnemer
    context_object_name = "deelnemers"
    paginate_by = 50

    allowed_sort_fields = {
        "naam",
        "-naam",
        "woonplaats",
        "-woonplaats",
    }

    def get_filter_data(self):
        """
        Geef de GET-data terug waarmee het filterformulier
        wordt opgebouwd.

        Wanneer is_uitgestroomd ontbreekt, worden standaard
        alleen niet-uitgestroomde deelnemers getoond.
        """
        filter_data = self.request.GET.copy()

        if "is_uitgestroomd" not in filter_data:
            filter_data["is_uitgestroomd"] = "false"

        return filter_data

    def get_queryset(self):
        today = timezone.localdate()

        active_since = (
            timezone.now()
            - timedelta(days=180)
        )

        third_last_ticket = (
            Ticket.objects
            .filter(
                deelnemer=OuterRef("pk"),
            )
            .order_by(
                "-activiteit__begin_datum"
            )
            .values(
                "activiteit__begin_datum"
            )[2:3]
        )

        outflow_exists = (
            DeelnemerUitstroom.objects
            .filter(
                deelnemer_id=OuterRef("pk"),
            )
        )

        methodiek_goal_exists = (
            HoofdDoel.objects
            .filter(
                deelnemer_id=OuterRef("pk"),
                type_doel=0,
            )
        )

        talent_goal_exists = (
            HoofdDoel.objects
            .filter(
                deelnemer_id=OuterRef("pk"),
                type_doel=1,
            )
        )

        queryset = (
            Deelnemer.objects
            .select_related(
                "aanmeld_locatie",
            )
            .annotate(
                aantal_tickets=Count(
                    "tickets",
                    distinct=True,
                ),
                aantal_methodiekpunten=Count(
                    "methodiekpunten",
                    distinct=True,
                ),
                third_last_ticket=Subquery(
                    third_last_ticket
                ),
                is_uitgestroomd_status=Exists(
                    outflow_exists
                ),
                heeft_methodiek_doel=Exists(
                    methodiek_goal_exists
                ),
                heeft_talent_doel=Exists(
                    talent_goal_exists
                ),
            )
            .exclude(
                naam__in=[
                    "NOG IN TE DELEN",
                    "OVERIG",
                ]
            )
        )

        self.filter_form = DeelnemerFilterForm(
            self.get_filter_data()
        )

        if self.filter_form.is_valid():
            queryset = self.apply_filters(
                queryset
            )

        queryset = self.apply_sorting(
            queryset
        )

        return queryset

    def apply_filters(self, queryset):
        actief = self.filter_form.cleaned_data.get(
            "actief"
        )

        in_methodiek = (
            self.filter_form.cleaned_data.get(
                "in_methodiek"
            )
        )

        is_uitgestroomd = (
            self.filter_form.cleaned_data.get(
                "is_uitgestroomd"
            )
        )

        woonplaats_zoek = (
            self.request.GET
            .get(
                "woonplaats_zoek",
                "",
            )
            .strip()
        )

        if woonplaats_zoek:
            queryset = queryset.filter(
                woonplaats__icontains=(
                    woonplaats_zoek
                )
            )

        active_since = (
            timezone.now()
            - timedelta(days=180)
        )

        active_filter = Q(
            aantal_tickets__gte=3,
            third_last_ticket__gte=active_since,
        )

        if actief == "true":
            queryset = queryset.filter(
                active_filter
            )
        elif actief == "false":
            queryset = queryset.exclude(
                active_filter
            )

        if in_methodiek == "true":
            queryset = queryset.filter(
                aantal_methodiekpunten__gte=1
            )
        elif in_methodiek == "false":
            queryset = queryset.filter(
                aantal_methodiekpunten=0
            )

        if is_uitgestroomd == "true":
            queryset = queryset.filter(
                is_uitgestroomd_status=True
            )
        elif is_uitgestroomd == "false":
            queryset = queryset.filter(
                is_uitgestroomd_status=False
            )

        return queryset

    def apply_sorting(self, queryset):
        requested_sort = self.request.GET.get(
            "sort",
            "naam",
        )

        if (
            requested_sort
            not in self.allowed_sort_fields
        ):
            requested_sort = "naam"

        self.current_sort = requested_sort

        if requested_sort == "woonplaats":
            return queryset.order_by(
                "woonplaats",
                "naam",
            )

        if requested_sort == "-woonplaats":
            return queryset.order_by(
                "-woonplaats",
                "naam",
            )

        if requested_sort == "-naam":
            return queryset.order_by(
                "-naam"
            )

        return queryset.order_by("naam")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(
            **kwargs
        )

        page_objects = context[
            "page_obj"
        ].object_list

        active_since = (
            timezone.now()
            - timedelta(days=180)
        )

        for deelnemer in page_objects:
            is_active = (
                deelnemer.aantal_tickets >= 3
                and deelnemer.third_last_ticket
                is not None
                and deelnemer.third_last_ticket
                >= active_since
            )

            deelnemer.actief = (
                "Ja"
                if is_active
                else "Nee"
            )

            deelnemer.in_methodiek = (
                "Ja"
                if (
                    deelnemer
                    .aantal_methodiekpunten
                    >= 1
                )
                else "Nee"
            )

            if deelnemer.woonplaats is None:
                deelnemer.woonplaats = ""

        context["form"] = self.filter_form

        context["huidige_sort"] = getattr(
            self,
            "current_sort",
            "naam",
        )

        context[
            "huidige_woonplaats_zoekterm"
        ] = self.request.GET.get(
            "woonplaats_zoek",
            "",
        )

        return context
 
@method_decorator(is_begeleider_required, name='dispatch')

class DeelnemerDetailView(DetailView):

    model = Deelnemer
    template_name = "core/deelnemer/deelnemer_detail.html"
    context_object_name = "deelnemer"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Haal de deelnemer op
        deelnemer = self.get_object()

        # Haal de laatste 10 activiteiten op waaraan de deelnemer heeft deelgenomen
        deelnemer_tickets = Ticket.objects.filter(deelnemer=deelnemer)
        alle_tickets = deelnemer_tickets.all()
        laatste_activiteiten = deelnemer_tickets.order_by('-activiteit__begin_datum')[:10]
        eerste_activiteit = deelnemer_tickets.order_by('activiteit__begin_datum').first()
        context['eerste_activiteit'] = eerste_activiteit
        context['laatste_activiteiten'] = laatste_activiteiten
        context['totale_tickets'] = len(alle_tickets)
        context['heeft_doelen'] = HoofdDoel.objects.filter(deelnemer=deelnemer).exists()
        dagen_terug = [365, 90, 30]
        nu = timezone.now()

        datums = {}
        for dagen in dagen_terug:
            begin_moment = nu - timedelta(days=dagen)
            resultaten = Ticket.objects.filter(deelnemer=deelnemer, activiteit__begin_datum__range=[begin_moment, nu])
            datums[dagen] = len(resultaten)
        #context["toekomstig"] = len(toekomstig)
        context['datums'] = datums
        context['uitgestroomd'] = DeelnemerUitstroom.objects.filter(deelnemer=deelnemer).exists()
        return context
    
@method_decorator(is_begeleider_required, name='dispatch')

class DeelnemerUpdateView(UpdateView):
    model = Deelnemer
    form_class = DeelnemerUpdateForm
    template_name = "core/deelnemer/deelnemer_update.html"
    context_object_name = "deelnemer"
    success_url = reverse_lazy('core:deelnemer_list')
    
@method_decorator(is_begeleider_required, name='dispatch')

class DeelnemerInstroomUpdateView(UpdateView):
    model = DeelnemerInstroom
    form_class = DeelnemerInstroomUpdateForm
    template_name = "core/deelnemer/deelnemer_instroom_update.html"
    context_object_name = "deelnemer"
    success_url = reverse_lazy('core:deelnemer_list')

@method_decorator(is_begeleider_required, name='dispatch')

class DeelnemerUitstroomCreateView(CreateView):
    model = DeelnemerUitstroom
    form_class = DeelnemerUitstroomForm
    template_name = "core/deelnemer/deelnemer_uitstroom_create.html"
    context_object_name = "deelnemer"
    success_url = reverse_lazy('core:deelnemer_list')
    
    def get(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        pk = kwargs.get("pk")
        deelnemer = Deelnemer.objects.get(pk=pk)
        context = {}
        form = DeelnemerUitstroomForm()

        context["deelnemer"] = deelnemer.naam
        context["form"] = form
        
        return render(request, template_name=self.template_name, context=context)

    def form_valid(self, form):
        pk = self.kwargs.get("pk")
        deelnemer = Deelnemer.objects.get(pk=pk)
        form.instance.deelnemer = deelnemer
        return super().form_valid(form)

@method_decorator(is_begeleider_required, name='dispatch')

class DeelnemerUitstroomDeleteView(DeleteView):
    model = DeelnemerUitstroom
    template_name = 'core/deelnemer/deelnemer_uitstroom_delete.html'
    success_url = reverse_lazy('core:deelnemer_list')
    context_object_name = "deelnemer"

    def post(self, request, *args, **kwargs):
        try:
            return super().delete(request, *args, **kwargs)
        except ProtectedError as e:
            # Hier wordt een ProtectedError afgevangen
            error_message = f"Kan het object niet verwijderen vanwege verwijzingen naar andere objecten:"
            # Voeg de gekoppelde objecten toe aan de foutmelding
            objecten = [naam for naam in e.protected_objects]
            return render(request, 'core/protect_error.html', {'error_message': error_message, 'objects': objecten})


@method_decorator(is_begeleider_required, name='dispatch')

class DeelnemerDeleteView(DeleteView):
    model = Deelnemer
    template_name = 'core/deelnemer/deelnemer_delete.html'
    success_url = reverse_lazy('core:deelnemer_list')
    
    def post(self, request, *args, **kwargs):
        try:
            return super().delete(request, *args, **kwargs)
        except ProtectedError as e:
            # Hier wordt een ProtectedError afgevangen
            error_message = f"Kan het object niet verwijderen vanwege verwijzingen naar andere objecten:"
            # Voeg de gekoppelde objecten toe aan de foutmelding
            objecten = [naam for naam in e.protected_objects]
            return render(request, 'core/protect_error.html', {'error_message': error_message, 'objects': objecten})

@method_decorator(is_begeleider_required, name='dispatch')

class DeelnemerZoekView(ListView):
    template_name = 'core/deelnemer/deelnemer_zoek.html'
    model = Deelnemer
    
@is_begeleider_required

def check_deelnemer(request):

    if request.method == 'GET':
        naam = request.GET.get('naam', '')
        exists = Deelnemer.objects.filter(naam=naam).exists()
        return JsonResponse({'exists': exists})

@method_decorator(is_begeleider_required, name='dispatch')

class SuggestiesAPI(View):

    def get(self, request, *args, **kwargs):
        zoekterm = request.GET.get('zoekterm', '')

        # Voer je logica uit om de lijst met deelnemers op te halen op basis van de zoekterm
        deelnemers = Deelnemer.objects.filter(naam__icontains=zoekterm).order_by("naam")

        # Maak een lijst van objecten met id en naam
        suggesties = [{'naam': deelnemer.naam, 'id': deelnemer.id, 'detail_url': reverse("core:deelnemer_detail", args=[deelnemer.id])} for deelnemer in deelnemers]

        # Retourneer de lijst van objecten als JSON
        return JsonResponse({'suggesties': suggesties})

@method_decorator(is_begeleider_required, name='dispatch')

class MeedoenRegelingListView(ListView):
    template_name = 'core/deelnemer/meedoenregeling_list.html'
    model = DeelnemerMeedoenRegeling
    ordering = ['deelnemer__naam']
    context_object_name = "deelnemers"
