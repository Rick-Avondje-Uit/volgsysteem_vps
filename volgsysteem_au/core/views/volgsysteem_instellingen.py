from django.utils.decorators import method_decorator
from django.views.generic import ListView, UpdateView
from core.models import VolgsysteemInstelling
from core.permissions import is_begeleider_required
from core.services.volgsysteem import (
    verwijder_alle_acties,
)


@method_decorator(is_begeleider_required, name='dispatch')
class VolgsysteemInstellingenListView(ListView):
    template_name = 'core/instellingen/instellingen.html'
    model = VolgsysteemInstelling
    ordering = ['-id']
    context_object_name="instellingen_list"
    
@method_decorator(is_begeleider_required, name='dispatch')
class VolgsysteemInstellingenDetailView(UpdateView):
    model = VolgsysteemInstelling
    template_name = "core/instellingen/instellingen_detail.html"
    context_object_name = "volgsysteem_instelling"

    fields = ["tijdsduur", "tijdsperiode"]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        verwijder_alle_acties()

        return response
