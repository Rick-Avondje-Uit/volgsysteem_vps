from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from core.models import Deelnemer, Plaats


@login_required
def deelnemer_email_lijst(request):
    zoekterm = request.GET.get("q", "").strip()
    hoofdlocatie = request.GET.get("hoofdlocatie", "").strip()

    deelnemers = (
        Deelnemer.objects
        .exclude(email__isnull=True)
        .exclude(email="")
        .select_related("aanmeld_locatie")
        .order_by("naam")
    )

    if zoekterm:
        deelnemers = deelnemers.filter(
            Q(naam__icontains=zoekterm)
            | Q(email__icontains=zoekterm)
        )

    if hoofdlocatie:
        deelnemers = deelnemers.filter(
            aanmeld_locatie_id=hoofdlocatie
        )

    locaties = Plaats.objects.order_by("naam")

    return render(
        request,
        "core/deelnemer/email_lijst.html",
        {
            "deelnemers": deelnemers,
            "locaties": locaties,
            "zoekterm": zoekterm,
            "hoofdlocatie": hoofdlocatie,
        },
    )