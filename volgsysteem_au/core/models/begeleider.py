from django.db import models
from .plaats import Plaats
from django.urls import reverse

class Begeleider(models.Model):
    naam = models.CharField(max_length=64)
    locatie = models.ForeignKey(Plaats, on_delete=models.SET_NULL, null=True)
    def __str__(self):
        return self.naam
    
    def get_absolute_url(self):
        return reverse("core:methodiek_list")
    
    class Meta:
        verbose_name_plural = "Begeleiders"
        verbose_name = "Begeleider"
