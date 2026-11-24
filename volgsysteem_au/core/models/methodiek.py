from django.db import models
from django.urls import reverse
from .deelnemer import Deelnemer
from .begeleider import Begeleider

class MethodiekPunten(models.Model):
    deelnemer = models.OneToOneField(Deelnemer, unique=True, on_delete=models.CASCADE)
    begeleider = models.ForeignKey(Begeleider, on_delete=models.SET_NULL, null=True)
    op_pauze = models.BooleanField(default=False)
    acties_choices = [(0, "eerste vragenlijst invullen"),
                        (1, "begin gesprek"),
                        (2, "drie maanden evaluatie"),
                        (3, "zes maanden evaluatie"),
                        (4, "negen maanden evaluatie"),
                        (5, "jaar evaluatie"),
                        (6, "verlengings gesprek 1"),
                        (7, "verlengings gesprek 2"),
                        (8, "afgerond")]
    eerst_volgende_actie = models.SmallIntegerField(choices=acties_choices)
    datum_vragenlijst_invullen = models.DateField(blank=True, null=True)
    begin_gesprek = models.DateField(blank=True, null=True, verbose_name='datum begin gesprek')
    drie_maanden_evaluatie = models.DateField(blank=True, null=True)
    zes_maanden_evaluatie = models.DateField(blank=True, null=True)
    negen_maanden_evaluatie = models.DateField(blank=True, null=True)
    jaar_evaluatie = models.DateField(blank=True, null=True)
    verlengings_gesprek_1 = models.DateField(blank=True, null=True)
    verlengings_gesprek_2 = models.DateField(blank=True, null=True)
    class Meta:
        verbose_name_plural = "Methodiek punten"
        verbose_name = "Methodiek punten"

    def get_absolute_url(self):
        return reverse('core:methodiek_detail', kwargs={'pk': self.deelnemer.pk})
    
    def __str__(self):
        if self.op_pauze:
            return f"de methodiek van {self.deelnemer} is gepauzeerd"
        

        statussen = [self.datum_vragenlijst_invullen, 
                     self.begin_gesprek, 
                     self.drie_maanden_evaluatie,
                     self.zes_maanden_evaluatie,
                     self.negen_maanden_evaluatie,
                     self.jaar_evaluatie,
                     self.verlengings_gesprek_1,
                     self.verlengings_gesprek_2]
        if self.eerst_volgende_actie == 8:
            return f"{self.deelnemer} heeft methodiek afgerond op {self.verlengings_gesprek_2}."
        
        if self.eerst_volgende_actie == 0:
            return f"{self.deelnemer} moet eerste vragenlijst nog invullen."
        choices = [choice[1] for choice in self.acties_choices]
        return f"status {self.deelnemer}: {choices[self.eerst_volgende_actie]} op {statussen[self.eerst_volgende_actie]}"
 

    @property
    def huidige_status(self):
        statussen = ["eerste vragenlijst invullen",
                        "begin gesprek",
                        "drie maanden evaluatie",
                        "zes maanden evaluatie",
                        "negen maanden evaluatie",
                        "jaar evaluatie",
                        'vervolg gesprek 1',
                        'vervolg gesprek 2',
                        "afgerond"]
        return statussen[self.eerst_volgende_actie]
    

    @property
    def huidige_status_datum(self):
        statussen = [self.datum_vragenlijst_invullen, 
                     self.begin_gesprek, 
                     self.drie_maanden_evaluatie,
                     self.zes_maanden_evaluatie,
                     self.negen_maanden_evaluatie,
                     self.jaar_evaluatie,
                     self.verlengings_gesprek_1,
                     self.verlengings_gesprek_2]
        
        if self.eerst_volgende_actie == 8:
            return None
        
        return statussen[self.eerst_volgende_actie]
    
    def __lt__(self, other):
        if self.huidige_status_datum is None and other.huidige_status_datum is None:
            return True
        
        if self.huidige_status_datum is None:
            return False
        
        if other.huidige_status_datum is None:
            return True
        return self.huidige_status_datum < other.huidige_status_datum
