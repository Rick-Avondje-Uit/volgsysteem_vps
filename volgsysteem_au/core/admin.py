from .models import Ticket, Deelnemer, Plaats, WoonPlaatsDeelnemer, Activiteit, DeelnemerInstroom, DeelnemerMeedoenRegeling, DeelnemerUitstroom, DeelnemerVolgsysteem, VolgsysteemInstelling, Acties, Begeleider, MethodiekPunten, RapportageDoel, DagRapportage, HoofdDoel, SubDoel
from django.db.models.functions import Lower
from django.contrib import admin

class ActiviteitAdmin(admin.ModelAdmin):
    list_display = ["naam", 'begin_datum', 'plaats', "tickets_verkocht"]
    search_fields = ["deelnemer__naam", 'begin_datum', 'plaats', "tickets_verkocht"]
    def tickets_verkocht(self, obj):
        return len(Ticket.objects.filter(activiteit=obj).all())
    
    ordering = ('-begin_datum', "plaats")


class TicketAdmin(admin.ModelAdmin):
    list_display = ('deelnemer_naam', 'activiteit_datum', 'activiteit_plaats', "activiteit_naam", "type_ticket", 'gekocht_op')
    ordering = ('-activiteit__begin_datum',)
    def deelnemer_naam(self, obj):
        if obj.deelnemer is not None:
            return obj.deelnemer.naam
        else:
            return "Anoniem"

    def activiteit_datum(self, obj):
        return obj.activiteit.datum

    def activiteit_plaats(self, obj):
        return obj.activiteit.plaats
    
    def activiteit_naam(self, obj):
        return obj.activiteit.naam


class WoonplaatsDeelnemerAdmin(admin.ModelAdmin):
    list_display = ['naam', 'aantal_deelnemers_die_er_wonen']

    def aantal_deelnemers_die_er_wonen(self, obj):
        return Deelnemer.objects.filter(woonplaats=obj.naam).count()

    aantal_deelnemers_die_er_wonen.short_description = "Aantal deelnemers"

class DeelnemerAdmin(admin.ModelAdmin):
    list_display = ['naam', 'mobiele_nummer', 'email']
    search_fields = ['naam', 'mobiele_nummer', 'email']
    def get_ordering(self, request):
        return [Lower('naam')]

class DeelnemerInstroomAdmin(admin.ModelAdmin):
    list_display = ['deelnemer', "contact_formulier_datum", "intake_datum"]
    def deelgenomen(self, obj):
        return obj.deelgenomen_aan_activiteiten

admin.site.register(Plaats)
admin.site.register(WoonPlaatsDeelnemer, WoonplaatsDeelnemerAdmin)
admin.site.register(Activiteit, ActiviteitAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Deelnemer, DeelnemerAdmin)
admin.site.register(DeelnemerInstroom, DeelnemerInstroomAdmin)
admin.site.register(DeelnemerMeedoenRegeling)
admin.site.register(DeelnemerVolgsysteem)
admin.site.register(DeelnemerUitstroom)
admin.site.register(VolgsysteemInstelling)
admin.site.register(Acties)
admin.site.register(Begeleider)
admin.site.register(MethodiekPunten)
admin.site.register(DagRapportage)
admin.site.register(HoofdDoel)
admin.site.register(SubDoel)
admin.site.register(RapportageDoel)