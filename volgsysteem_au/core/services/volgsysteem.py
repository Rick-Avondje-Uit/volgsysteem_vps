from datetime import date
from django.utils import timezone
from core.models import Acties, Deelnemer, DeelnemerVolgsysteem


def verwijder_alle_acties() -> int:
    """
    Verwijder alle berekende acties.

    Geeft het aantal verwijderde Acties-records terug.
    """
    aantal_verwijderd, _ = Acties.objects.all().delete()

    return aantal_verwijderd


def verwijder_acties_voor_deelnemer(
    deelnemer: Deelnemer,
) -> int:
    """
    Verwijder alle berekende acties van één deelnemer.

    Geeft het aantal verwijderde Acties-records terug.
    """
    aantal_verwijderd, _ = Acties.objects.filter(
        deelnemer=deelnemer,
    ).delete()

    return aantal_verwijderd


def verwijder_acties_voor_deelnemers(
    deelnemers,
) -> int:
    """
    Verwijder de berekende acties van meerdere deelnemers.

    Dubbele deelnemers worden door de databasefiltering automatisch
    maar één keer meegenomen.
    """
    deelnemer_ids = {
        deelnemer.pk
        for deelnemer in deelnemers
        if deelnemer is not None and deelnemer.pk is not None
    }

    if not deelnemer_ids:
        return 0

    aantal_verwijderd, _ = Acties.objects.filter(
        deelnemer_id__in=deelnemer_ids,
    ).delete()

    return aantal_verwijderd

def bepaal_minimaal_aantal_dagen(
    geselecteerde_datum: date | None,
) -> int:
    """
    Bepaal hoeveel dagen terug deelnemers getoond mogen worden.

    Zonder geselecteerde datum blijft het bestaande standaardgedrag
    van maximaal 30 dagen terug behouden.
    """
    if geselecteerde_datum is None:
        return -30

    vandaag = timezone.localdate()

    return (geselecteerde_datum - vandaag).days


def haal_te_benaderen_deelnemers(
    *,
    geselecteerde_datum: date | None = None,
    aantal_dagen_vooruit: int = 7,
) -> list[DeelnemerVolgsysteem]:
    """
    Selecteer en sorteer deelnemers die binnen de ingestelde
    actietermijn vallen.
    """
    minimaal_aantal_dagen = bepaal_minimaal_aantal_dagen(
        geselecteerde_datum,
    )

    resultaten = []

    deelnemers = DeelnemerVolgsysteem.objects.all()

    for deelnemer_volgsysteem in deelnemers:
        dagen_tot_actie = (
            deelnemer_volgsysteem.dagen_tot_actie
        )

        if dagen_tot_actie is None:
            continue

        if dagen_tot_actie > aantal_dagen_vooruit:
            continue

        if dagen_tot_actie < minimaal_aantal_dagen:
            continue

        resultaten.append(
            (
                deelnemer_volgsysteem,
                dagen_tot_actie,
            )
        )

    resultaten.sort(
        key=lambda resultaat: resultaat[1]
    )

    return [
        deelnemer_volgsysteem
        for deelnemer_volgsysteem, _ in resultaten
    ]

