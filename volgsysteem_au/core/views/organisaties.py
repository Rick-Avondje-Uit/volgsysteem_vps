from typing import Any
import pandas as pd
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import View
from core.models import Deelnemer
from core.permissions import is_begeleider_required

@method_decorator(is_begeleider_required, name='dispatch')
class OrganisatiesOverzichtView(View):
    template_name = 'core/organisatie_overzicht.html'
    context_object_name="deelnemer"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        context: dict[str, Any] = {}
        organisatie_data = Deelnemer.objects.all()
        
        data: list[tuple[str, str | None, int, str]]= [
            (d.zorgorganisatie.title(), d.zorgorganisatie_locatie, 1, d.naam) for d in organisatie_data if d.zorgorganisatie is not None and d.zorgorganisatie != "Algemeen: deelnemers"
            ]
        
        if not data:
            context['data'] = "<p>Geen organisatiegegevens beschikbaar.</p>"
            return render(request, template_name=self.template_name, context=context)
        
        df = pd.DataFrame(data, columns=['zorgorganisatie', 'extra info','aantal', 'deelnemer'])
        df['extra info'].fillna('', inplace=True)
        
        df_grouped = df.groupby(['zorgorganisatie', 'extra info'])[['aantal']].sum()
        df_grouped = df_grouped.sort_index(level=['zorgorganisatie', 'extra info'], ascending=[True, True])
        context['data'] = df_grouped.fillna(0).astype(int).to_html(classes='table table-striped', border=1)

        df_grouped_2 = df.groupby(['zorgorganisatie', 'deelnemer'])[['aantal']].sum()
        df_grouped_2 = df_grouped_2.sort_index(level=['zorgorganisatie', 'deelnemer'], ascending=[True, True])
        context['organisatie_per_deelnemer'] = df_grouped_2.astype(int).to_html(classes='table table-striped', border=1)
        
        return render(request, template_name=self.template_name, context=context)