from datetime import timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, UpdateView
from core.forms import DeelnemerUpdateForm
from core.models import DagRapportage, Deelnemer, HoofdDoel, Ticket, DeelnemerUitstroom

class DoelenListView(LoginRequiredMixin, ListView):
    template_name = 'core/deelnemer/deelnemer_doelen_list.html'
    model = HoofdDoel
    context_object_name="doelen"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        deelnemer = get_object_or_404(Deelnemer, email=self.request.user.email)
        context['deelnemer'] = deelnemer
        context['heeft_doelen'] = HoofdDoel.objects.filter(deelnemer__id = deelnemer.id).exists()
        doelen = HoofdDoel.objects.filter(deelnemer__id = deelnemer.id).filter().all()
        methodiek_doelen = doelen.filter(type_doel=0).all()
        talent_ontwikkel_doelen = doelen.filter(type_doel=1).all()
        context['methodiek_doelen'] = methodiek_doelen
        context['talent_doelen'] = talent_ontwikkel_doelen
        return context

class DeelnemerUpdateView(LoginRequiredMixin, UpdateView):
    model = Deelnemer
    form_class = DeelnemerUpdateForm
    template_name = "core/deelnemer/deelnemer_update.html"
    context_object_name = "deelnemer"
    success_url = reverse_lazy('core:index')


    def get_object(self, queryset = ...):
        return Deelnemer.objects.get(email=self.request.user.email)
    
class RapportagesListView(LoginRequiredMixin, ListView):
    template_name = 'core/rapportage/rapportage_list.html'
    model = DagRapportage
    context_object_name="rapportages"

    def get_queryset(self):
        return (
            DagRapportage.objects.filter(
                deelnemer__email=self.request.user.email,
                zichtbaar_voor_deelnemer=True,
            )
            .order_by("-datum")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        deelnemer = get_object_or_404(
            Deelnemer,
            email=self.request.user.email,
        )

        context["rapportages_aanwezig"] = (
            self.object_list.exists()
        )

        context['deelnemer_id'] = deelnemer.id

        return context

class DeelnemerDetailView(LoginRequiredMixin, DetailView):
    model = Deelnemer
    template_name = "core/deelnemer/deelnemer_detail.html"
    context_object_name = "deelnemer"

    def get_object(self, queryset=None):
        return get_object_or_404(
            Deelnemer,
            email=self.request.user.email,
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        deelnemer = self.object

        # Haal de laatste 10 activiteiten op waaraan de deelnemer heeft deelgenomen
        deelnemer_tickets = Ticket.objects.filter(deelnemer=deelnemer)
        laatste_activiteiten = deelnemer_tickets.order_by('-activiteit__begin_datum')[:10]
        eerste_activiteit = deelnemer_tickets.order_by('activiteit__begin_datum').first()
        context['eerste_activiteit'] = eerste_activiteit
        context['laatste_activiteiten'] = laatste_activiteiten
        context['totale_tickets'] = deelnemer_tickets.count()
        context['heeft_doelen'] = HoofdDoel.objects.filter(deelnemer=deelnemer).exists()
        dagen_terug = [365, 90, 30]
        nu = timezone.now()
        datums = {}
        for dagen in dagen_terug:
            begin_moment = nu - timedelta(days=dagen)
            datums[dagen] = Ticket.objects.filter(deelnemer=deelnemer, activiteit__begin_datum__range=[begin_moment, nu]).count()
        context['datums'] = datums
        context['uitgestroomd'] = DeelnemerUitstroom.objects.filter(deelnemer=deelnemer).exists()
        return context
    


