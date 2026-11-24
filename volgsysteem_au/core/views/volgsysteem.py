from datetime import timedelta
from typing import Any
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, UpdateView
from core.forms import VolgsysteemListViewForm
from core.models import DeelnemerVolgsysteem, VolgsysteemInstelling
from core.permissions import is_begeleider_required
from core.services.volgsysteem import (
    haal_te_benaderen_deelnemers,
    verwijder_acties_voor_deelnemer,
    verwijder_alle_acties,
)

@method_decorator(is_begeleider_required, name='dispatch')
class DeelnemerVolgsysteemListView(ListView):

    template_name = 'core/deelnemer/deelnemer_volgsysteem_list.html'
    model = DeelnemerVolgsysteem
    selected_date = None
    aantal_dagen_vooruit = 7
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object_list = self.get_queryset()
        if request.GET.get('ververs'):
           verwijder_alle_acties()

        # Roep de 'get' methode van de ouderklasse aan om de basiscontext te krijgen
        context = self.get_context_data()
        # Voeg hier eventuele extra context-gegevens toe of update bestaande gegevens
        context['selected_date'] = self.selected_date
        context['num_dagen_vooruit'] = self.aantal_dagen_vooruit

        # Render de pagina met de bijgewerkte context
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = VolgsysteemListViewForm(request.POST)

        if form.is_valid():
            self.selected_date = form.cleaned_data['date_field']
            self.aantal_dagen_vooruit = form.cleaned_data['num_dagen_vooruit']

            return self.get(request, *args, **kwargs)

        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)

    def get_queryset(self):
        deelnemers = DeelnemerVolgsysteem.objects.all()
        return deelnemers

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        deelnemers = haal_te_benaderen_deelnemers(
            geselecteerde_datum=self.selected_date,
            aantal_dagen_vooruit=self.aantal_dagen_vooruit,
        )

        context["deelnemers"] = deelnemers
        context["selected_date"] = self.selected_date
        context["num_dagen_vooruit"] = (
            self.aantal_dagen_vooruit
        )
        context["huidige_datum"] = timezone.localdate()

        initial_data = {
            "date_field": (
                    self.selected_date
                    or timezone.localdate()
                    - timedelta(days=30)
            ),
            "num_dagen_vooruit": (
                self.aantal_dagen_vooruit
            ),
        }

        context["form"] = VolgsysteemListViewForm(
            initial=initial_data,
        )

        return context

@method_decorator(is_begeleider_required, name='dispatch')   
class DeelnemerVolgsysteemDetailView(DetailView):
    model = DeelnemerVolgsysteem
    template_name = "core/deelnemer/deelnemer_volgsysteem_detail.html"
    context_object_name = "deelnemer"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["actiepunten"] = VolgsysteemInstelling.objects.order_by("-id").all()
        gebruiker = self.get_object()
        gebruiker.dagen_tot_actie_individueel
        context["actie_datum1"] = gebruiker.actie_datum_1
        context["actie_datum2"] = gebruiker.actie_datum_2
        context["actie_datum3"] = gebruiker.actie_datum_3
        return context

@method_decorator(is_begeleider_required, name='dispatch')
class DeelnemerVolgsysteemUpdateView(UpdateView):
    model = DeelnemerVolgsysteem
    template_name = "core/deelnemer/deelnemer_volgsysteem_update.html"
    context_object_name = "deelnemer"
    fields = ["deelnemer_actie1", "deelnemer_actie2", "deelnemer_actie3"]

    def post(self, request, *args, **kwargs):
        response = super().post(
            request,
            *args,
            **kwargs,
        )

        deelnemer_volgsysteem = self.object

        verwijder_acties_voor_deelnemer(
            deelnemer_volgsysteem.deelnemer,
        )

        return response

    def get_success_url(self) -> str:
        return reverse_lazy("core:deelnemer_volgsysteem_list")