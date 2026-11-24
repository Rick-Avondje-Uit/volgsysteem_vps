from django.db.models.deletion import ProtectedError
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from core.forms import BegeleiderToevoegenForm
from core.models import Begeleider
from core.permissions import is_begeleider_required

@method_decorator(is_begeleider_required, name='dispatch')

class BegeleiderToevoegenView(CreateView):
    login_url = 'login/'
    redirect_field_name = 'core/methodiek/methodiek_punten_list.html'
    template_name = "core/begeleider/begeleider_add.html"
    form_class = BegeleiderToevoegenForm
    model = Begeleider

@method_decorator(is_begeleider_required, name='dispatch')

class BegeleiderListView(ListView):
    template_name = 'core/begeleider/begeleider_list.html'
    model = Begeleider
    context_object_name="begeleiders"


@method_decorator(is_begeleider_required, name='dispatch')

class BegeleiderUpdateView(UpdateView):
    model = Begeleider
    template_name = "core/begeleider/begeleider_update.html"
    context_object_name = "begeleider"

    fields = ["naam", "locatie"]

@method_decorator(is_begeleider_required, name='dispatch')

class BegeleiderDeleteView(DeleteView):
    model = Begeleider
    template_name = 'core/begeleider/begeleider_delete.html'
    success_url = reverse_lazy('core:begeleider_list')
    
    def post(self, request, *args, **kwargs):
        try:
            return super().delete(request, *args, **kwargs)
        except ProtectedError as e:
            # Hier wordt een ProtectedError afgevangen
            error_message = f"Kan het object niet verwijderen vanwege verwijzingen naar andere objecten:"
            # Voeg de gekoppelde objecten toe aan de foutmelding
            objecten = list(e.protected_objects)
            return render(request, 'core/protect_error.html', {'error_message': error_message, 'objects': objecten})
