from django.db import models
from django.urls import reverse
from .deelnemer import Deelnemer

class VolgsysteemInstelling(models.Model):
    naam = models.CharField(max_length=255, unique=True)
    tijdsduur = models.IntegerField()
    eenheid_keuzes = [
        ('d', 'dagen'),
        ('w', 'weken'),
        ('m', 'maanden'),
    ]
    tijdsperiode = models.CharField(max_length=1, choices=eenheid_keuzes)

    def __str__(self):
        return self.naam
    
    class Meta:
        verbose_name_plural = "Actie types"
        verbose_name = "Actie"

    def get_absolute_url(self):
        return reverse('core:instellingen')

class Acties(models.Model):
    deelnemer = models.OneToOneField(Deelnemer, on_delete=models.CASCADE, primary_key=True, related_name="deelnemer_actie")
    actie = models.ForeignKey(VolgsysteemInstelling, on_delete=models.CASCADE, blank=True, related_name="actie")
    datum = models.DateField(blank=True, null=True)
    class Meta:
        verbose_name_plural = "Acties"
        verbose_name = "Actie"

    def __str__(self):
        return f"{self.deelnemer.naam} {self.actie} op {self.datum}"

