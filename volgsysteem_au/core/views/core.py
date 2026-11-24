from core.models import Deelnemer, HoofdDoel, Ticket
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.utils import timezone
from datetime import datetime, timedelta

class IndexView(LoginRequiredMixin, View):
    template_name="core/main_page.html"
    def get(self, request, *args, **kwargs):

        if request.user.is_staff or request.user.groups.filter(name="Begeleider").exists():
            return render(request, self.template_name)
        elif Deelnemer.objects.filter(email=request.user.email).exists():
            deelnemer = Deelnemer.objects.get(email=request.user.email)
            context = {'deelnemer': deelnemer}
            context['heeft_doelen'] = HoofdDoel.objects.filter(deelnemer = deelnemer).exists()
            doelen = HoofdDoel.objects.filter(deelnemer=deelnemer).filter().all()
            methodiek_doelen = doelen.filter(type_doel=0).all()
            talent_ontwikkel_doelen = doelen.filter(type_doel=1).all()
            context['methodiek_doelen'] = methodiek_doelen
            context['talent_doelen'] = talent_ontwikkel_doelen

            deelnemer_tickets = Ticket.objects.filter(deelnemer=deelnemer)
            alle_tickets = deelnemer_tickets.all()
            laatste_activiteiten = deelnemer_tickets.order_by('-activiteit__begin_datum')[:10]
            eerste_activiteit = deelnemer_tickets.order_by('activiteit__begin_datum').first()
            context['eerste_activiteit'] = eerste_activiteit
            context['laatste_activiteiten'] = laatste_activiteiten
            context['totale_tickets'] = len(alle_tickets)
            context['heeft_doelen'] = HoofdDoel.objects.filter(deelnemer=deelnemer).exists()
            dagen_terug = [365, 90, 30]
            nu = datetime.now()
            nu = timezone.make_aware(nu)
            datums = {}
            for dagen in dagen_terug:
                begin_moment = nu - timedelta(days=dagen)
                resultaten = Ticket.objects.filter(deelnemer=deelnemer, activiteit__begin_datum__range=[begin_moment, nu])
                datums[dagen] = len(resultaten)
            #context["toekomstig"] = len(toekomstig)
            context['datums'] = datums
            return render(request, 'core/deelnemer_detail.html', context=context)
        else:
            return render(request, template_name=self.template_name)
  