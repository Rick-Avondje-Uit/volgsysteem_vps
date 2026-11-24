from typing import Any
import pandas as pd
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import View
from core.models import DeelnemerInstroom
from core.permissions import is_begeleider_required

@method_decorator(is_begeleider_required, name='dispatch')
class DeelnemerInstroomPerMaand(View):
    template_name = 'core/deelnemer/instroom_overzicht_per_maand.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        context: dict[str, Any] = {}
        instroom_data = DeelnemerInstroom.objects.all().order_by('-intake_datum')
        
        # 1. Lijst opbouwen 
        data: list[tuple[int, int, str, int]] = [
            (d.intake_datum.year, d.intake_datum.month, d.deelnemer.aanmeld_locatie.naam, 1) for d in instroom_data if d.intake_datum is not None
            ] 
        
        if not data:
            context['data'] = "<p>Geen instroomgegevens beschikbaar.</p>"
            return render(request, template_name=self.template_name, context=context)
        
        df = pd.DataFrame(data, columns=['jaar', 'maand', 'plaats', 'aantal'])
        
        # 2. Selecteer 'aantal' voor de aanroep
        df_grouped = df.groupby(['jaar', 'maand', 'plaats'])['aantal'].sum().unstack()
       
        # 3. Sorteren op multiIndex 
        df_grouped = df_grouped.sort_index(level=['jaar', 'maand'], ascending=[False, False])
        
        # 4. HTML genreren met nette style
        context['data'] = df_grouped.fillna(0).astype(int).to_html(classes='table table-striped', border=1)
        
        return render(request, template_name=self.template_name, context=context)
