from django.db import models
from django.urls import reverse
from datetime import datetime
from django.utils.timezone import make_aware
from dateutil.relativedelta import relativedelta
from .plaats import Plaats
class Deelnemer(models.Model):
    naam = models.CharField(max_length=64)
    naam_tickets = models.CharField(max_length=64)
    belangrijke_info = models.TextField(blank=True, null=True)

    KEUZES = [
        ('man', 'Man'),
        ("vrouw", "Vrouw"),
        ("non", 'Non-binair'),
        ('overig', "Overig"),
        ("onb", "Niet opgegeven")
    ]

    geslacht = models.CharField(max_length=6, choices=KEUZES, default='onb')
    geboortedatum = models.DateField(blank=True, null=True)
    woonplaats = models.CharField(blank=True, null=True, max_length=64, verbose_name='Woonplaats')
    aanmeld_locatie = models.ForeignKey(Plaats, on_delete=models.PROTECT)
    zorgorganisatie = models.CharField(max_length=64, blank=True, null=True)
    zorgorganisatie_locatie = models.CharField(max_length=250, blank=True, null=True)  
    mobiele_nummer = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    meenemen_in_volgsysteem = models.BooleanField(verbose_name='Volgen met volgsysteem', blank=True, null=True, default=True)
    @property
    def voornaam(self):
        return self.naam.split()[0]
    
    @property
    def achternaam(self):
        return self.naam.split()[-1]
    
    @property
    def tussenvoegsel(self):
        if len(self.naam.split()) == 2:
            return None
        else:
            return " ".join(self.naam.split()[1:-1])
        
    def get_absolute_url(self):
        return reverse('core:deelnemer_detail', kwargs={'pk': self.pk})
    
    def __str__(self):
        return self.naam
    
    def __lt__(self, other):
        return self.naam < other.naam

from .ticket import Ticket
class DeelnemerInstroom(models.Model):
    deelnemer = models.OneToOneField(Deelnemer, on_delete=models.CASCADE, primary_key=True, related_name="deelnemer_instroom")
    contact_formulier_datum = models.DateField(blank=True, null=True)
    intake_datum = models.DateField(default=datetime.now, null=True)
    heeft_ons_gevonden_via = models.CharField(max_length=64, blank=True, null=True)
    zorgorganisatie_start = models.CharField(max_length=64, blank=True, null=True)
    tickets = None
    class Meta:
        verbose_name_plural = "Deelnemers instroom"
        verbose_name = "Deelnemer instroom"
    
    @property
    def deelgenomen_aan_activiteiten(self):
        if not self.tickets:
            self.tickets = Ticket.objects.filter(deelnemer=self.deelnemer).all()
        return len(self.tickets) > 0
    def __str__(self):
        if self.deelgenomen_aan_activiteiten:
            return f"{self.deelnemer.naam} had intake op {self.intake_datum} en heeft deelgenomen aan activiteiten"
        else:
            return f"{self.deelnemer.naam} had intake op {self.intake_datum} en heeft nog niet deelgenomen"

from .volgsysteem import VolgsysteemInstelling, Acties
class DeelnemerVolgsysteem(models.Model):
    deelnemer = models.OneToOneField(Deelnemer, on_delete=models.CASCADE, primary_key=True, related_name="deelnemer_volgsysteem")

    deelnemer_actie1 = models.DateField(blank=True, null=True)
    deelnemer_actie2 = models.DateField(blank=True, null=True)
    deelnemer_actie3 = models.DateField(blank=True, null=True)

    actie_datum = None
    actie_datum_1 = None
    actie_datum_2 = None
    actie_datum_3 = None
    def __str__(self):
        return self.deelnemer.naam    
    
    class Meta:
        verbose_name_plural = "Deelnemers info volgsysteem"
        verbose_name = "Deelnemer info volgsysteem"
    
    def get_actie_date(self, tijdsperiode, tijdsduur):
        if tijdsperiode == "d":
            delta = relativedelta(days=tijdsduur)
        elif tijdsperiode == "w":
            delta = relativedelta(weeks=tijdsduur)
        elif tijdsperiode == "m":
            delta = relativedelta(months=tijdsduur)
        return delta
    
    @property
    def volgende_actie_stap(self):
        if not self.deelnemer_actie1:
            return VolgsysteemInstelling.objects.order_by("-id").first().naam
        if not self.deelnemer_actie2:
            return VolgsysteemInstelling.objects.order_by("-id").all()[1].naam
        if not self.deelnemer_actie3:
            return VolgsysteemInstelling.objects.order_by("-id").all()[2].naam
        return None
    
    @property
    def volgende_actie_stap_item(self):
        if not self.deelnemer_actie1:
            return VolgsysteemInstelling.objects.order_by("-id").first()
        if not self.deelnemer_actie2:
            return VolgsysteemInstelling.objects.order_by("-id").all()[1]
        if not self.deelnemer_actie3:
            return VolgsysteemInstelling.objects.order_by("-id").all()[2]
        return None
    
    # individueel aan eind van funcie/property naam:
    # voer berekeningen helemaal uit voor alle data, kost alleen iets meer tijd
    def volgende_actie_datum(self, datum_laatst_contact):
        volgende_actie = self.volgende_actie_stap_item
        if Acties.objects.filter(deelnemer=self.deelnemer, actie=volgende_actie).exists():
            self.actie_datum = Acties.objects.filter(deelnemer=self.deelnemer, actie=volgende_actie).first().datum
            return
        if not DeelnemerInstroom.objects.filter(deelnemer=self.deelnemer).exists():
            return None
        deelgenomen_aan_activiteit = DeelnemerInstroom.objects.get(deelnemer=self.deelnemer).deelgenomen_aan_activiteiten
        if not deelgenomen_aan_activiteit:
            intake_data = DeelnemerInstroom.objects.get(deelnemer=self.deelnemer)
            if not intake_data.intake_datum:
                datum_laatst_contact = intake_data.contact_formulier_datum
            else:
                datum_laatst_contact = intake_data.intake_datum
        if datum_laatst_contact is None:
            datum_laatst_contact = "2000-01-01"
        if isinstance(datum_laatst_contact, str):
            datum_laatst_contact = make_aware(datetime.strptime(datum_laatst_contact, "%Y-%m-%d"))
            
        # in het geval er geen acties zijn ondernomen: 
                
        actie1 = VolgsysteemInstelling.objects.order_by("-id").first()
        actie = actie1
        delta1 = self.get_actie_date(actie1.tijdsperiode, actie1.tijdsduur)
        actie_datum = datum_laatst_contact + delta1

        self.actie_datum_1 = actie_datum
        # zodra de eerste actie al is ondernomen: tel er de tweede tijdsperiode bovenop
        if self.deelnemer_actie1:
            actie2 = VolgsysteemInstelling.objects.order_by("-id").all()[1]
            actie = actie2
            if isinstance(actie_datum, datetime):
                actie_datum = actie_datum.date()
            delta2 = self.get_actie_date(actie2.tijdsperiode, actie2.tijdsduur)

            actie_datum = max(actie_datum, self.deelnemer_actie1)
            actie_datum += delta2
            self.actie_datum_2 = actie_datum

        if self.deelnemer_actie2:            
            actie3 = VolgsysteemInstelling.objects.order_by("-id").last()
            actie = actie3
            delta3 = self.get_actie_date(actie3.tijdsperiode, actie3.tijdsduur)
            if isinstance(actie_datum, datetime):
                actie_datum = actie_datum.date()
            actie_datum = max(actie_datum, self.deelnemer_actie2)
            actie_datum += delta3
            self.actie_datum_3 = actie_datum

        # acties zijn allemaal al ondernomen, nu hoeft avondje uit niets meer te doen
        if self.deelnemer_actie3:
            actie_datum = None
            actie = None
        self.actie_datum = actie_datum
        if actie is not None:
            if not Acties.objects.filter(deelnemer=self.deelnemer, actie = actie).exists():
                Acties.objects.create(deelnemer=self.deelnemer, actie=actie, datum=actie_datum)
        return actie_datum
    
    def volgende_actie_datum_individueel(self, datum_laatst_contact):
        
        deelgenomen_aan_activiteit = DeelnemerInstroom.objects.get(deelnemer=self.deelnemer).deelgenomen_aan_activiteiten
        if not deelgenomen_aan_activiteit:
            if not self.intake_datum:
                datum_laatst_contact = self.contact_formulier_datum
            else:
                datum_laatst_contact = self.intake_datum
        if datum_laatst_contact is None:
            datum_laatst_contact = "2000-01-01"
        if isinstance(datum_laatst_contact, str):
            datum_laatst_contact = make_aware(datetime.strptime(datum_laatst_contact, "%Y-%m-%d"))
            
        # in het geval er geen acties zijn ondernomen: 
                
        actie1 = VolgsysteemInstelling.objects.order_by("-id").first()
        delta1 = self.get_actie_date(actie1.tijdsperiode, actie1.tijdsduur)
        actie_datum = datum_laatst_contact + delta1
        self.actie_datum_1 = actie_datum.date()
        # zodra de eerste actie al is ondernomen: tel er de tweede tijdsperiode bovenop
        if self.deelnemer_actie1:
            actie2 = VolgsysteemInstelling.objects.order_by("-id").all()[1]
            delta2 = self.get_actie_date(actie2.tijdsperiode, actie2.tijdsduur)
            actie_datum = max(actie_datum.date(), self.deelnemer_actie1)
            actie_datum += delta2
            self.actie_datum_2 = actie_datum

        if self.deelnemer_actie2:            
            actie3 = VolgsysteemInstelling.objects.order_by("-id").last()
            delta3 = self.get_actie_date(actie3.tijdsperiode, actie3.tijdsduur)
            actie_datum = max(actie_datum, self.deelnemer_actie2)
            actie_datum += delta3
            self.actie_datum_3 = actie_datum

        # acties zijn allemaal al ondernomen, nu hoeft avondje uit niets meer te doen
        if self.deelnemer_actie3:
            actie_datum = None
        self.actie_datum = actie_datum
        return actie_datum
    
    @property
    def dagen_tot_actie(self):
        
        if self.deelnemer_actie3:
            return None
        
        dt = make_aware(datetime.now()).date()
        if not self.actie_datum:
            volgende_actie = self.volgende_actie_stap_item
            if Acties.objects.filter(deelnemer=self.deelnemer, actie=volgende_actie).exists():
                self.actie_datum = Acties.objects.filter(deelnemer=self.deelnemer, actie=volgende_actie).first().datum
            else:
                # zorg dat actie_datum gezet wordt, dit wordt gedaan door de functie self.volgende_actie_datum() uit te voeren met laatste ticket datum
                tickets = Ticket.objects.filter(deelnemer=self.deelnemer).all().order_by('-activiteit__begin_datum').all()
                if len(tickets) == 0:
                    datum = make_aware(datetime.now())
                else:
                    datum = tickets[0].activiteit.datum
                self.volgende_actie_datum(datum)
                
        if isinstance(self.actie_datum, datetime):
            self.actie_datum = self.actie_datum.date()
        res = None
        # het kan gebeuren dat iemand geen tickets
        if self.actie_datum is None:
            res = None
        else:
            res = int((self.actie_datum - dt).total_seconds() // (60*60*24))
        
        return res
    
    @property
    def dagen_tot_actie_individueel(self):
        
        if self.deelnemer_actie3:
            return None
        
        dt = make_aware(datetime.now()).date()
        #if not self.actie_datum:
        # zorg dat actie_datum gezet wordt, dit wordt gedaan door de functie self.volgende_actie_datum() uit te voeren met laatste ticket datum
        tickets = Ticket.objects.filter(deelnemer=self.deelnemer).all().order_by('-activiteit__begin_datum').all()
        if len(tickets) == 0:
            datum = make_aware(datetime.now())
        else:
            datum = tickets[0].activiteit.datum
        self.volgende_actie_datum_individueel(datum)
                
        if isinstance(self.actie_datum, datetime):
            self.actie_datum = self.actie_datum.date()

        res = int((self.actie_datum - dt).total_seconds() // (60*60*24))
        return res
    
    def __lt__(self, other):
        return self.dagen_tot_actie <= other.dagen_tot_actie


class DeelnemerUitstroom(models.Model):
    deelnemer = models.OneToOneField(Deelnemer, on_delete=models.CASCADE, primary_key=True, related_name="deelnemer_uitstroom")
    reden_uitstroming = models.TextField(blank=True, null=True)
    wil_op_hoogte_blijven = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Deelnemers info uitstroom"
        verbose_name = "Deelnemer info uitstroom"

    def __str__(self):
        return f"{self.deelnemer.naam}: {self.reden_uitstroming}" 

class DeelnemerMeedoenRegeling(models.Model):
    deelnemer = models.OneToOneField(Deelnemer, on_delete=models.CASCADE, primary_key=True, related_name="deelnemer_meedoeregeling")  
    meedoenregeling_nummer = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.deelnemer.naam}: {self.meedoenregeling_nummer}"
    
    class Meta:
        verbose_name_plural = "Deelnemers info meedoenregeling"
        verbose_name = "Deelnemer info meedoenregeling"
    