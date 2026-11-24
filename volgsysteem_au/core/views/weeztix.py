from __future__ import annotations
import secrets
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from core.services.weeztix.oauth import build_authorization_url
from core.services.weeztix.exceptions import WeeztixError
from core.services.weeztix.token_service import WeeztixTokenService


WEEZTIX_OAUTH_STATE_SESSION_KEY = "weeztix_oauth_state"


@login_required
def weeztix_redirect(request: HttpRequest) -> HttpResponse:
    """Start de Weeztix OAuth Authorization Code-flow."""
    state = secrets.token_urlsafe(32)
    request.session[WEEZTIX_OAUTH_STATE_SESSION_KEY] = state
    request.session.modified = True

    redirect_uri = settings.WEEZTIX_REDIRECT_URI

    authorization_url = build_authorization_url(
        state=state,
        redirect_uri=redirect_uri,
    )
    return redirect(authorization_url)


@login_required
def weeztix_callback(request: HttpRequest) -> HttpResponse:
    """Controleer de callback en sla de Weeztix-tokens versleuteld op."""
    oauth_error = request.GET.get("error")
    if oauth_error:
        error_description = request.GET.get(
            "error_description",
            oauth_error,
        )
        request.session.pop(
            WEEZTIX_OAUTH_STATE_SESSION_KEY,
            None,
        )
        messages.error(
            request,
            "De Weeztix-koppeling is niet voltooid: "
            f"{error_description}.",
        )
        return redirect("core:ticket_list")

    received_state = request.GET.get("state")
    expected_state = request.session.pop(
        WEEZTIX_OAUTH_STATE_SESSION_KEY,
        None,
    )

    if not expected_state:
        messages.error(
            request,
            "De Weeztix OAuth-sessie ontbreekt of is verlopen. "
            "Start de koppeling opnieuw.",
        )
        return redirect("core:ticket_list")

    if (
        not received_state
        or not secrets.compare_digest(received_state, expected_state)
    ):
        messages.error(
            request,
            "De Weeztix OAuth-controle is mislukt. "
            "De state-waarde is ongeldig.",
        )
        return redirect("core:ticket_list")

    authorization_code = request.GET.get("code")
    if not authorization_code:
        messages.error(
            request,
            "Weeztix heeft geen authorization code teruggegeven.",
        )
        return redirect("core:ticket_list")

    redirect_uri = request.build_absolute_uri(
        reverse("core:weeztix_callback")
    )
    token_service = WeeztixTokenService()

    try:
        token = token_service.exchange_authorization_code(
            code=authorization_code,
            redirect_uri=redirect_uri,
        )
        token_service.save_for_user(
            user=request.user,
            token=token,
            scope="",
        )
    except WeeztixError as exc:
        messages.error(
            request,
            "De Weeztix-koppeling kon niet worden opgeslagen: "
            f"{exc}",
        )
        return redirect("core:ticket_list")

    messages.success(
        request,
        "De Weeztix-koppeling is succesvol opgeslagen.",
    )
    return redirect("core:ticket_list")
