from django.test import TestCase

from core.models import Acties
from core.services.volgsysteem import (
    verwijder_acties_voor_deelnemer,
    verwijder_alle_acties,
)

