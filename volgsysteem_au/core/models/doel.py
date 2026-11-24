from django.db import models
from .deelnemer import Deelnemer
from datetime import datetime
from django.utils import timezone

class HoofdDoel(models.Model):
    deelnemer = models.ForeignKey(Deelnemer, on_delete=models.CASCADE)
    TYPE_DOEL = [
        (0, 'Methodiek'),
        (1, 'Talentontwikkelplek'),
    ]
    type_doel = models.PositiveIntegerField(choices=TYPE_DOEL, default=0)
    tekst = models.TextField()
    datum_aangemaakt = models.DateField(default=datetime.now, blank=True, null=True)
    datum_afgerond = models.DateField(null=True, blank=True)
    hoofddoel_afgerond = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        tekst = self.tekst if len(self.tekst) < 50 else self.tekst[:50] + '...'
        return f"Hoofddoel {self.deelnemer}: {tekst}"

    class Meta:
        verbose_name_plural = "Hoofddoelen"
        verbose_name = "Hoofddoel"

    def save(self, *args, **kwargs):
        if self.pk:
            orig = HoofdDoel.objects.get(pk=self.pk)
            if self.hoofddoel_afgerond and not orig.hoofddoel_afgerond:
                self.datum_afgerond = timezone.now().date()
            elif not self.hoofddoel_afgerond and orig.hoofddoel_afgerond:
                self.datum_afgerond = None
        else:
            # Eerste keer opslaan
            if self.hoofddoel_afgerond:
                self.datum_afgerond = timezone.now().date()
        super().save(*args, **kwargs)


class SubDoel(models.Model):
    hoofddoel = models.ForeignKey(HoofdDoel, on_delete=models.CASCADE, related_name='subdoelen')
    tekst = models.TextField()
    datum_aangemaakt = models.DateField(default=datetime.now, null=True, blank=True)
    datum_afgerond = models.DateField(null=True, blank=True)
    subdoel_afgerond = models.BooleanField(default=False, blank=True, null=True)
    
    def __str__(self):
        tekst = self.tekst if len(self.tekst) < 50 else self.tekst[:50] + '...'
        return f"subdoel {self.hoofddoel.deelnemer}: {tekst}"

    class Meta:
        verbose_name_plural = "Subdoelen"
        verbose_name = "Subdoel"

    def save(self, *args, **kwargs):
        if self.pk:
            orig = SubDoel.objects.get(pk=self.pk)
            if self.subdoel_afgerond and not orig.subdoel_afgerond:
                self.datum_afgerond = timezone.now().date()
            elif not self.subdoel_afgerond and orig.subdoel_afgerond:
                self.datum_afgerond = None
        else:
            # Eerste keer opslaan
            if self.subdoel_afgerond:
                self.datum_afgerond = timezone.now().date()
        super().save(*args, **kwargs)
