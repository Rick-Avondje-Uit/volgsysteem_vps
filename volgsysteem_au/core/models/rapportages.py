from django.db import models
from .deelnemer import Deelnemer
from datetime import datetime
from .doel import SubDoel

class DagRapportage(models.Model):
    ingevuld_door = models.CharField(max_length=64)
    deelnemer = models.ForeignKey(Deelnemer, on_delete=models.CASCADE)
    datum = models.DateTimeField(default=datetime.now)
    zichtbaar_voor_deelnemer = models.BooleanField(default=True, verbose_name='Zichtbaar voor deelnemer')
    tekst = models.TextField()
    def __str__(self):
        return f"{self.deelnemer.naam} {self.datum.strftime('%Y-%m-%d')}:  {self.tekst[:50]}"
    
    class Meta:
        verbose_name_plural = "rapportages"
        verbose_name = "rapportage"

class RapportageDoel(models.Model):
    subdoel = models.ForeignKey(SubDoel, on_delete=models.CASCADE, related_name='rapportages')
    datum = models.DateField(default=datetime.now, blank=True)
    tekst = models.TextField()
    begeleider = models.CharField(max_length=50, blank=True, default='Avondje Uit')
    def __str__(self):
        tekst = self.tekst if len(self.tekst) < 50 else self.tekst[:50] + '...'
        return f"rapportage bij doel {self.subdoel.hoofddoel.deelnemer}: {tekst}"

    class Meta:
        verbose_name_plural = "rapportages bij doelen"
        verbose_name = "rapportage bij doel"

