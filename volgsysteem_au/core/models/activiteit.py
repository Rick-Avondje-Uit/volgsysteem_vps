from django.db import models
from .plaats import Plaats
from django.urls import reverse

class Activiteit(models.Model):
    guid = models.CharField(max_length=36, unique=True)
    begin_datum = models.DateTimeField()
    eind_datum = models.DateTimeField()
    KEUZES = [
        ('vakantie', 'Vakantie'),
        ('evenement', 'Evenement'),
        ('activiteit', 'Activiteit'),
        ('overig', 'Overig'),
        ("mentaal", "Mentale weerbaarheid"),
        ("brainstorm", "Brainstorm")
    ]
    plaats = models.ForeignKey(Plaats, on_delete=models.PROTECT) # voorkomt dat plaats verwijderd wordt als er activiteiten aan gelinkt zijn
    type_activiteit = models.CharField(max_length=10, choices=KEUZES, default='activiteit', blank=True)
    naam = models.CharField(max_length=128)
    bedrag = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    @property
    def tijdsduur_uren(self):
        dagen_verschil = self.eind_datum - self.begin_datum
        uren, rest = divmod(dagen_verschil.total_seconds(), 3600)
        minuten = rest // 60

        uren = str(int(uren))
        minuten = str(int(minuten))        
        minuten = str.zfill(minuten, 2)
        return f"{uren}:{minuten}"
    
    @property
    def jaar(self):
        return self.begin_datum.year
    
    @property
    def maand(self):
        return self.begin_datum.month
    
    @property
    def dag(self):
        return self.begin_datum.day
    
    @property
    def datum(self):
        return self.begin_datum.date()
    
    def __str__(self):
        return f"{self.naam}: {self.datum} ({self.plaats})"
    
    def get_absolute_url(self):
        return reverse('core:activiteit_list')

    def __lt__(self, other):
        return self.datum < other.datum

    class Meta:
        verbose_name_plural = "Activiteiten"
