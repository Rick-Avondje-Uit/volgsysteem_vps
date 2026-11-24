from typing import Any
import pandas as pd
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import View, ListView, UpdateView
from core.models import Deelnemer
from core.permissions import is_begeleider_required
from survey.models import Answer, Response


@method_decorator(is_begeleider_required, name='dispatch')
class VragenlijstResultatenDeelnemerDetailView(View):

    template_name="core/vragenlijst/vragenlijst_resultaten_deelnemer.html"

    def get(self, request, *args, **kwargs):

        # responses Rico
        deelnemer = Deelnemer.objects.get(id=self.kwargs.get("pk"))
        responses = Response.objects.filter(deelnemer=deelnemer).all().order_by("-created")
        if not responses.exists():
            context = {"no_df": True}
            return render(request, template_name=self.template_name, context=context)
        guids = [response.interview_uuid for response in responses]

        datums = [response.created.strftime("%d%m%Y") for response in responses]
        datums.insert(0, "datum ingevuld")
        antwoorden_deelnemer = []
        categorie_types = ["Zelfvertrouwen", "Communicatieve vaardigheden", "Samenwerken",
                           "Initiatief nemen", "Invoelend vermogen", "Verantwoordelijkheid nemen",
                           "Overige vragen"]
        alle_open_antwoorden = []
        for it, vragenlijst in enumerate(guids):
            antwoorden_vragenlijst = []
            #antwoorden = Answer.objects.filter(response__interview_uuid = vragenlijst).filter(question__type="radio").order_by("question__order").all()
            antwoorden = Answer.objects.filter(response__interview_uuid = vragenlijst).order_by("question__order").all()
            antwoorden_open = Answer.objects.filter(response__interview_uuid = vragenlijst).filter(question__type="text").order_by("question__order").all()
            alle_open_antwoorden.append([ant.body for ant in antwoorden_open])

            if it == 0:
                for antwoord in antwoorden:
                    antwoorden_vragenlijst.append(antwoord.question.text.replace("\r\n", ""))
                    
                antwoorden_deelnemer.append(tuple(antwoorden_vragenlijst))
                antwoorden_vragenlijst = []

                for antwoord in antwoorden:
                    antwoorden_vragenlijst.append(antwoord.question.category.name)

                antwoorden_deelnemer.append(tuple(antwoorden_vragenlijst))
                antwoorden_vragenlijst = []

                for antwoord in antwoorden:
                    antwoorden_vragenlijst.append(antwoord.question.type)
                antwoorden_deelnemer.append(tuple(antwoorden_vragenlijst))
                antwoorden_vragenlijst = []
            
            # laat alle antwoorden in dataframe
            for antwoord in antwoorden:
                ant = antwoord.body.replace("\r\n", "<br>")
                ant = " ".join(ant.split("-"))
                if len(ant) < 2:
                    ant = "Geen opmerkingen"
                antwoorden_vragenlijst.append(ant)
            antwoorden_deelnemer.append(tuple(antwoorden_vragenlijst))
        context = {"open_antwoorden": alle_open_antwoorden}
        df = pd.DataFrame(antwoorden_deelnemer)
        
        datums.insert(1, "cat")
        datums.insert(2, "type")
        for it, cat in enumerate(categorie_types):
            df_temp = df
            df_temp = df_temp.T
            df_temp.columns = datums
            df_temp = df_temp[df_temp['cat'] == cat]
            df_temp = df_temp.drop(['cat'], axis=1)
            # Genereer automatisch gegenereerde HTML met pandas
            html = df_temp.to_html(index=False,classes='my-table', table_id='my-table')
            # Voeg CSS-stijlen toe om het hover-effect te implementeren
            html = html.replace('<head>', '<head>')
            context[f"data_{it}"] = html
            
        
        return render(request, template_name=self.template_name, context=context)
    
@method_decorator(is_begeleider_required, name='dispatch')
class VragenlijstDeelnemersListView(ListView):
    template_name = 'core/vragenlijst/vragenlijst_deelnemers_list.html'
    model = Response
    ordering = ['deelnemer__naam']
    context_object_name="deelnemers"
    
    def get_queryset(self):
        # Haal alle unieke waarden van my_field op
        res = Response.objects.values_list('deelnemer', flat=True).distinct()
        res = Deelnemer.objects.filter(id__in=res).order_by("naam").all()
        return res
    
@method_decorator(is_begeleider_required, name='dispatch')
class VragenlijstListView(ListView):
    template_name = 'core/vragenlijst/vragenlijst_ingevuld_list.html'
    model = Response
    ordering = ['-created']
    context_object_name="vragenlijsten"
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        objects = context.get('object_list')
        deelnemer_met_naam = []
        for obj in objects:
            antwoord = Answer.objects.filter(response__interview_uuid = obj.interview_uuid).order_by("question__order").first()
            deelnemer_met_naam.append((antwoord.body, obj.deelnemer.naam, obj.created, obj.id))
        context['deelnemers_met_naam'] = deelnemer_met_naam
        return context
    
@method_decorator(is_begeleider_required, name='dispatch')
class VragenlijstDeelnemerUpdateView(UpdateView):
    model = Response
    template_name = "core/vragenlijst/vragenlijst_deelnemer_toekennen.html"
    context_object_name = "deelnemer"

    fields = ["deelnemer"]

    success_url = reverse_lazy("core:resultaten_vragenlijst_ingevuld")
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        antwoord = Answer.objects.filter(response__interview_uuid = context['object'].interview_uuid).order_by("question__order").first()
        context['opgegeven_naam'] = antwoord.body
        return context