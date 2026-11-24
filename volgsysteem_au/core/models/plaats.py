from django.db import models

class Plaats(models.Model):
    naam = models.CharField(max_length=32, unique=True)
    shop_naam = models.CharField(max_length = 64, blank=True, null=True)
    def __str__(self):
        return self.naam
    
    class Meta:
        verbose_name_plural = "Plaatsen"
        verbose_name = "Plaats"


class WoonPlaatsDeelnemer(models.Model):
    naam = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.naam

    class Meta:
        verbose_name_plural = 'Woonplaatsen'
        verbose_name = 'Woonplaats'
