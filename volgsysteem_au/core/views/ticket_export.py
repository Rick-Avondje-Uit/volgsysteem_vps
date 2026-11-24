from core.models import Ticket
from django.http import HttpResponse
from django.views import View
from core.forms import TicketDownloadForm
import pandas as pd
from core.permissions import is_begeleider_required
from django.utils.decorators import method_decorator
from io import BytesIO as IO
from django.shortcuts import render

@method_decorator(is_begeleider_required, name='dispatch')
class TicketExcelView(View):
    template_name = "core/ticket/download_tickets.html"
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"form: TicketDownloadForm()"})
    
    def post(self, request, **kwargs):
        form = TicketDownloadForm(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {"form": form })

        begin_datum = form.cleaned_data['begin_datum']
        eind_datum = form.cleaned_data['eind_datum']
        plaatsen = form.cleaned_data['plaats_keuze']
        type_activiteit = form.cleaned_data['type_activiteit_keuze']

        ticket_data = Ticket.objects.all()
        if begin_datum:
            ticket_data = ticket_data.filter(activiteit__begin_datum__gte=begin_datum)
        if eind_datum:
            ticket_data = ticket_data.filter(activiteit__begin_datum__lte=eind_datum)
        if plaatsen:
            ticket_data = ticket_data.filter(activiteit__plaats__in=plaatsen)
        if type_activiteit:
            ticket_data = ticket_data.filter(activiteit__type_activiteit__in=type_activiteit)

        # Creëer een DataFrame met de gewenste gegevens
        data = {
            'Activiteit': [ticket.activiteit.naam for ticket in ticket_data],
            "Datum activiteit": [ticket.activiteit.begin_datum.date() for ticket in ticket_data],
            "Jaar": [ticket.activiteit.jaar for ticket in ticket_data],
            "Maand": [ticket.activiteit.maand for ticket in ticket_data],
            "Plaats activiteit": [ticket.activiteit.plaats for ticket in ticket_data],
            "Type activiteit": [ticket.activiteit.get_type_activiteit_display() for ticket in ticket_data],
            'Deelnemer Naam': [ticket.deelnemer.naam if ticket.deelnemer else "verwijderde gebruiker" for ticket in ticket_data],
            'Type ticket': [ticket.get_type_ticket_display() for ticket in ticket_data],
        }
        df = pd.DataFrame(data)



        excel_file = IO()

        xlwriter = pd.ExcelWriter(excel_file, engine='openpyxl')

        df.to_excel(xlwriter, 'tickets.xlsx', index=False)

        xlwriter.close()

        # important step, rewind the buffer or when it is read() you'll get nothing
        # but an error message when you try to open your zero length file in Excel
        excel_file.seek(0)

        # set the mime type so that the browser knows what to do with the file
        response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        # set the file name in the Content-Disposition header
        response['Content-Disposition'] = 'attachment; filename=tickets.xlsx'

        return response