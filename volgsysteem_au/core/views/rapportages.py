from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import View, CreateView, DeleteView, UpdateView
from core.forms import RapportageToevoegenForm, DoelRapportageToevoegenForm
from core.models import DagRapportage, Deelnemer, RapportageDoel, SubDoel
from core.permissions import (is_begeleider_required)


@method_decorator(is_begeleider_required, name='dispatch')
class RapportageCreateView(CreateView):
    model = DagRapportage
    form_class = RapportageToevoegenForm
    template_name = "core/rapportage/rapportage_add.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['deelnemer_id'] = self.kwargs['pk']
        return context

    def form_valid(self, form):
        deelnemer = get_object_or_404(
            Deelnemer,
            pk=self.kwargs['pk'],
        )

        form.instance.deelnemer = deelnemer

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('core:rapportage_list', kwargs={'pk': self.object.deelnemer.id})
    
@method_decorator(is_begeleider_required, name='dispatch')
class RapportageUpdateView(UpdateView):
    template_name = 'core/rapportage/rapportage_update.html'
    model = DagRapportage
    fields = ['ingevuld_door', 'datum', 'zichtbaar_voor_deelnemer', 'tekst']
    context_object_name = 'rapportage'
    def get_success_url(self):
        return reverse('core:rapportage_list', kwargs={'pk': self.object.deelnemer.id})
   
@method_decorator(is_begeleider_required, name='dispatch')
class RapportageDeleteView(DeleteView):
    model = DagRapportage
    template_name = 'core/rapportage/rapportage_delete.html'

    def get_success_url(self):
        return reverse('core:rapportage_list', kwargs={'pk': self.object.deelnemer.id})
    
@method_decorator(is_begeleider_required, name='dispatch')
class DoelRapportageCreateView(CreateView):
    model = RapportageDoel
    form_class = DoelRapportageToevoegenForm
    template_name = "core/rapportage/doel_rapportage_add.html"
    context_object_name = 'doel'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subdoel = get_object_or_404(
            SubDoel,
            pk=self.kwargs['pk'],)

        context['doel'] = subdoel
        context['deelnemer_id'] = subdoel.hoofddoel.deelnemer.id

        return context
    
    def form_valid(self, form):
        subdoel = get_object_or_404(
            SubDoel,
            pk=self.kwargs['pk'],
        )
        form.instance.subdoel = subdoel

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('core:deelnemer_doelen_list', kwargs={'pk': self.object.subdoel.hoofddoel.deelnemer.id})

@method_decorator(is_begeleider_required, name='dispatch')
class DoelRapportageUpdateView(UpdateView):

    model = RapportageDoel
    form_class = DoelRapportageToevoegenForm # zelfde velden als 
    template_name = "core/rapportage/doel_rapportage_update.html"

    def form_valid(self, form):
        rapportage = get_object_or_404(
            RapportageDoel,
            pk=self.kwargs['pk'],
        )
        
        form.instance.subdoel = rapportage.subdoel

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('core:deelnemer_doelen_list', kwargs={'pk': (self.object.subdoel.hoofddoel.deelnemer.id)})

@method_decorator(is_begeleider_required, name='dispatch')
class RapportageListView(View):

    template_name = 'core/rapportage/rapportage_list.html'

    def get(self, request, **kwargs):

        deelnemer_id = kwargs.get('pk')

        rapportages = (DagRapportage.objects.filter(deelnemer = deelnemer_id).order_by('-datum'))

        context = {
            'rapportages': rapportages,
            'rapportage_aanwezig': rapportages.exists(),
            'deelnemer_id': deelnemer_id,
        }

        return render(request, self.template_name, context=context)

    

@method_decorator(is_begeleider_required, name='dispatch')
class DoelRapportageDeleteView(DeleteView):
    model = RapportageDoel
    template_name = 'core/rapportage/doel_rapportage_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['deelnemer_id'] = (self.object.subdoel.hoofddoel.deelnemer.id)
        return context

    def get_success_url(self):
        return reverse('core:deelnemer_doelen_list', kwargs={'pk': (self.object.subdoel.hoofddoel.deelnemer.id)})
    
