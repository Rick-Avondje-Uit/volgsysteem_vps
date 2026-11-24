from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from core.forms import HoofdDoelToevoegenForm, SubDoelToevoegenForm
from core.models import HoofdDoel, SubDoel, Deelnemer
from core.permissions import is_begeleider_required

@method_decorator(is_begeleider_required, name='dispatch')
class HoofdDoelCreateView(CreateView):
    model = HoofdDoel
    form_class = HoofdDoelToevoegenForm
    template_name = 'core/rapportage/hoofddoel_add.html'
    pk = None
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['deelnemer_id'] = self.kwargs['pk']
        return context

    def form_valid(self, form):
        self.pk = self.kwargs['pk']
        deelnemer = get_object_or_404(Deelnemer, pk=self.kwargs['pk'])
        form.instance.deelnemer = deelnemer
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('core:deelnemer_doelen_list', kwargs={'pk': self.pk})

@method_decorator(is_begeleider_required, name='dispatch')
class HoofdDoelListView(ListView):
    template_name = 'core/deelnemer/deelnemer_doelen_list.html'
    model = HoofdDoel
    context_object_name="doelen"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        deelnemer = get_object_or_404(
            Deelnemer,
            pk=self.kwargs["pk"],
        )

        doelen = HoofdDoel.objects.filter(
            deelnemer=deelnemer
        )

        context["deelnemer"] = deelnemer
        context["heeft_doelen"] = doelen.exists()
        context["methodiek_doelen"] = doelen.filter(
            type_doel=0
        )
        context["talent_doelen"] = doelen.filter(
            type_doel=1
        )

        return context


@method_decorator(is_begeleider_required, name='dispatch')
class HoofdDoelUpdateView(UpdateView):
    model = HoofdDoel
    template_name = 'core/rapportage/hoofddoel_update.html'

    def get_success_url(self):
        return reverse(
            'core:deelnemer_doelen_list',
            kwargs={'pk': self.kwargs['pk']},
        )


@method_decorator(is_begeleider_required, name='dispatch')
class HoofdDoelDeleteView(DeleteView):
    model = HoofdDoel
    template_name = "core/rapportage/hoofddoel_delete.html"

    def get_success_url(self):
        return reverse(
            "core:deelnemer_doelen_list",
            kwargs={
                "pk": self.object.deelnemer_id,
            },
        )

@method_decorator(is_begeleider_required, name='dispatch')
class SubDoelCreateView(CreateView):
    model = SubDoel
    form_class = SubDoelToevoegenForm
    template_name = 'core/rapportage/subdoel_add.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        hoofddoel = get_object_or_404(
            HoofdDoel,
            pk=self.kwargs['pk']
        )

        context['pk'] = hoofddoel.pk
        context['hoofddoel'] = hoofddoel

        return context


    def form_valid(self, form):
        hoofddoel = get_object_or_404(
            HoofdDoel,
            pk=self.kwargs["pk"],
        )

        form.instance.hoofddoel = hoofddoel

        return super().form_valid(form)

    def get_success_url(self):
        hoofddoel = get_object_or_404(
            HoofdDoel,
            pk=self.kwargs["pk"],
        )

        return reverse(
            "core:deelnemer_doelen_list",
            kwargs={
                "pk": hoofddoel.deelnemer.pk,
            },
        )

@method_decorator(is_begeleider_required, name='dispatch')
class SubdoelUpdateView(UpdateView):
    model = SubDoel
    form_class = SubDoelToevoegenForm # bewerken bevat zelfde veld, dus mag toevoegenform gebruiken
    template_name = "core/rapportage/subdoel_update.html"
    context_object_name = "subdoel"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['deelnemer_id'] = SubDoel.objects.get(pk=self.kwargs['pk']).deelnemer.id
        return context
    
    def get_success_url(self):
        return reverse('core:deelnemer_doelen_list', kwargs={'pk': self.object.hoofddoel.deelnemer_id})
    
