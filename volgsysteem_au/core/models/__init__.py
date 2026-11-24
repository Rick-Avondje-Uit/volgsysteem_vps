from django.utils import timezone
from .activiteit import Activiteit, Plaats
from .begeleider import Begeleider
from .deelnemer import DeelnemerVolgsysteem, DeelnemerUitstroom, DeelnemerMeedoenRegeling, DeelnemerInstroom, Deelnemer
from .doel import SubDoel, HoofdDoel
from .methodiek import MethodiekPunten
from .plaats import WoonPlaatsDeelnemer
from .rapportages import DagRapportage, RapportageDoel
from .ticket import Ticket
from .volgsysteem import VolgsysteemInstelling, Acties

__all__ = [
    "Activiteit",
    "Plaats",
    "Begeleider",
    "Deelnemer",
    "DeelnemerInstroom",
    "DeelnemerMeedoenRegeling",
    "DeelnemerUitstroom",
    "DeelnemerVolgsysteem",
    "HoofdDoel",
    "SubDoel",
    "MethodiekPunten",
    "WoonPlaatsDeelnemer",
    "DagRapportage",
    "RapportageDoel",
    "Ticket",
    "VolgsysteemInstelling",
    "Acties",
]

def get_current_day():
    return timezone.now().strftime("%d/%m/%Y")
