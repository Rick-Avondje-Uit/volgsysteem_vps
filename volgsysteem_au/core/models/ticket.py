from django.db import models
from .deelnemer import Deelnemer

class Ticket(models.Model):
    # voor nu gewoon barcode, hashen geeft te grote waarde op om op te slaan en barcode ticket is toereikent
    hash_value = models.CharField(max_length=64, blank=True)
    activiteit = models.ForeignKey("Activiteit", on_delete=models.CASCADE)
    deelnemer_naam_ticket = models.CharField(max_length=64) # to be able to use fuzzy comparison and show typed and found matches
    deelnemer = models.ForeignKey(Deelnemer, on_delete=models.SET_NULL, blank=True, null=True, default="NOG IN TE DELEN", related_name="tickets")
    gekocht_op = models.DateTimeField(blank=True, null=True)
    bedrag = models.DecimalField(max_digits=6, decimal_places=2)
    TYPE_TICKETS = [
        (0, 'Reguliere ticket'),
        (1, 'Meedoen regeling'),
        (2, 'Gratis Ticket'),
        (3, 'Overig')
    ]
    type_ticket = models.PositiveIntegerField(choices=TYPE_TICKETS, default=0)
    woonplaats_deelnemer = models.ForeignKey('WoonPlaatsDeelnemer', on_delete=models.PROTECT, blank=True, null=True)
    def __lt__(self, other):
        return self.gekocht_op <= other.gekocht_op

    def __str__(self):
        return f"{self.activiteit.naam}:{self.deelnemer}"
    