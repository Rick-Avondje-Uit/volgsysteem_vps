from typing import Any
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect, get_object_or_404
from core.models import MethodiekPunten, Deelnemer
from django.views.generic import ListView, DetailView, UpdateView, CreateView
from django.http import HttpRequest, HttpResponse, Http404, JsonResponse
from django.db.models import Q
from datetime import datetime
from dateutil.relativedelta import relativedelta
from core.forms import MethodiekFilterForm, MethodiekPuntenToevoegenForm
from django.views.decorators.csrf import csrf_exempt
from core.permissions import is_begeleider_required
from django.utils.decorators import method_decorator

@method_decorator(is_begeleider_required, name='dispatch')
class MethodiekPuntenCreateView(CreateView):
    template_name = "core/methodiek/methodiek_add.html"
    form_class = MethodiekPuntenToevoegenForm
    model = MethodiekPunten
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Hier sorteren we de personen op naam in het formulier
        form.fields['deelnemer'].queryset = Deelnemer.objects.order_by('naam')
        return form
@method_decorator(is_begeleider_required, name='dispatch')
class MethodiekPuntenListView(ListView):

    template_name = 'core/methodiek/methodiek_punten_list.html'

    def get(self, request, *args, **kwargs):
        form = MethodiekFilterForm(request.GET)
        objecten = self.get_objecten(form)
        context = {'form': form, 'objecten': objecten, 'huidige_datum': datetime.today().date()}
        return render(request, self.template_name, context)

    def get_objecten(self, form):
        if form.is_valid():
            begeleider = form.cleaned_data['begeleider_keuze']
            alle_punten = form.cleaned_data['toon_afgeronde_trajecten']
            gepauzeerde_punten = form.cleaned_data['toon_gepauzeerde_trajecten']
            if begeleider:
                objecten = MethodiekPunten.objects.filter(begeleider=begeleider)

            else:
                objecten = MethodiekPunten.objects.all()

            if not alle_punten:
                objecten = objecten.filter(eerst_volgende_actie__lt=8)

            if not gepauzeerde_punten:
                objecten = objecten.filter(op_pauze=False)
        else:
            objecten = MethodiekPunten.objects.filter(Q(eerst_volgende_actie__lt=8)).filter(op_pauze=False)
        objecten = objecten.exclude(deelnemer__deelnemer_uitstroom__isnull=False)
        objecten = sorted(objecten)
        return objecten

@method_decorator(is_begeleider_required, name='dispatch')
class MethodiekPuntenDetailView(ListView):
    model = MethodiekPunten
    template_name = "core/methodiek/methodiek_punten_detail.html"

    def get_object(self, queryset=None):
        return get_object_or_404(
            MethodiekPunten,
            deelnemer__id=self.kwargs["pk"],
        )


    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        methodiek = self.get_object()

        context["methodiek"] = methodiek
        context['naam'] = methodiek.deelnemer.naam
        context['id'] = methodiek.deelnemer.id
        context['begeleider'] = methodiek.begeleider.naam
        context["status"] = methodiek.huidige_status
        context['pause'] = methodiek.op_pauze
        return context

@method_decorator(is_begeleider_required, name='dispatch')
class MethodiekPuntenActieUitgevoerd(DetailView, UpdateView):
    model = MethodiekPunten
    template_name = "core/methodiek/methodiek_punten_uitgevoerd.html"
    fields = ["eerst_volgende_actie", "datum_vragenlijst_invullen", 
              "begin_gesprek", "drie_maanden_evaluatie", "zes_maanden_evaluatie", 
              "negen_maanden_evaluatie", "jaar_evaluatie", "verlengings_gesprek_1", "verlengings_gesprek_2"]

    context_object_name = "object"
    datum_velden = ["datum_vragenlijst_invullen", "begin_gesprek", "drie_maanden_evaluatie", "zes_maanden_evaluatie", 
              "negen_maanden_evaluatie", "jaar_evaluatie", "verlengings_gesprek_1", "verlengings_gesprek_2"]
    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        super().post(request, *args, **kwargs)
        obj = self.get_object()
        if obj.eerst_volgende_actie == 8:
            return redirect("core:methodiek_list")
        
        if request.POST.get("afronden"):
            obj.eerst_volgende_actie = 8
            obj.save()
            return redirect("core:methodiek_list")

        obj.eerst_volgende_actie += 1
        if obj.eerst_volgende_actie < 8:
            setattr(obj, self.datum_velden[obj.eerst_volgende_actie], datetime.now().date() + relativedelta(months=3)) 
        obj.save()

        return redirect("core:methodiek_list")
    
    def get_object(self, queryset=None):
        return get_object_or_404(
            MethodiekPunten,
            deelnemer__id=self.kwargs["pk"],
        )
    
@method_decorator(is_begeleider_required, name='dispatch')
class MethodiekPuntenUpdateView(UpdateView):

    model = MethodiekPunten
    template_name = "core/methodiek/methodiek_punten_update.html"
    context_object_name = "methodiek"

    fields = ["begeleider", "op_pauze", "eerst_volgende_actie", "datum_vragenlijst_invullen", 
              "begin_gesprek", "drie_maanden_evaluatie", "zes_maanden_evaluatie", 
              "negen_maanden_evaluatie", "jaar_evaluatie", "verlengings_gesprek_1", "verlengings_gesprek_2"]
    
    def get_object(self, queryset= None):
        return get_object_or_404(
            MethodiekPunten,
            deelnemer__id=self.kwargs["pk"],
        )

    

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        methodiek = self.get_object()

        context['naam'] = methodiek.deelnemer.naam
        context['id'] = methodiek.deelnemer.id
        context['begeleider'] = methodiek.begeleider.naam
        context["status"] = methodiek.huidige_status
        context['pause'] = methodiek.op_pauze
        return context
    
    def get(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        if not MethodiekPunten.objects.filter(deelnemer__id = self.kwargs["pk"]).exists():
            raise Http404("Deze gebruiker zit niet in de methodiek")
        return super().get(request, *args, **kwargs)

# TODO: check JavaScript voor exempt
@csrf_exempt
def check_duplicates(request):
    if request.method == 'POST':
        selected_value = request.POST.get('selected_value', None)
        if selected_value:
            selected_value = int(selected_value)
        # Voer de duplicaatcontrole uit
        is_duplicate = MethodiekPunten.objects.filter(deelnemer__id = selected_value).exists()

        return JsonResponse({'duplicate': is_duplicate})

    return JsonResponse({'error': 'Invalid request method'})
