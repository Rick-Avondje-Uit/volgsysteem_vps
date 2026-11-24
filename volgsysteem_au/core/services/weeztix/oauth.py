# core/services/weeztix/oauth.py

from __future__ import annotations

from urllib.parse import urlencode

from django.conf import settings

from .exceptions import WeeztixAuthenticationError


def build_authorization_url(
    *,
    state: str,
    redirect_uri: str,
) -> str:
    """
    Bouw de Weeztix OAuth2 authorization-URL.

    De gebruiker wordt naar deze URL gestuurd om de applicatie
    toestemming te geven toegang te krijgen tot Weeztix.

    Args:
        state:
            Willekeurige state-waarde waarmee de callback wordt
            gecontroleerd tegen CSRF.

        redirect_uri:
            De callback-URL waar Weeztix de gebruiker na
            autorisatie naar terugstuurt.

    Returns:
        De volledige Weeztix authorization-URL.

    Raises:
        WeeztixAuthenticationError:
            Wanneer vereiste OAuth-instellingen of argumenten
            ontbreken.
    """

    authorization_url = getattr(
        settings,
        "WEEZTIX_AUTHORIZATION_URL",
        None,
    )

    client_id = getattr(
        settings,
        "WEEZTIX_CLIENT_ID",
        None,
    )

    if not authorization_url:
        raise WeeztixAuthenticationError(
            "WEEZTIX_AUTHORIZATION_URL ontbreekt."
        )

    if not client_id:
        raise WeeztixAuthenticationError(
            "WEEZTIX_CLIENT_ID ontbreekt."
        )

    if not state:
        raise WeeztixAuthenticationError(
            "De OAuth state-waarde ontbreekt."
        )

    if not redirect_uri:
        raise WeeztixAuthenticationError(
            "De Weeztix redirect_uri ontbreekt."
        )

    parameters = {
        "response_type": "code",
        "client_id": str(client_id),
        "redirect_uri": str(redirect_uri),
        "state": str(state),
    }

    separator = (
        "&"
        if "?" in authorization_url
        else "?"
    )

    return (
        f"{authorization_url}"
        f"{separator}"
        f"{urlencode(parameters)}"
    )
