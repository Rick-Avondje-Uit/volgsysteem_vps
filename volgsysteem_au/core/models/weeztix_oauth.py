from django.conf import settings
from django.db import models


class WeeztixOAuthToken(models.Model):
    """
    Versleutelde OAuth-tokens voor een Weeztix-koppeling.

    De database bevat uitsluitend encrypted tokenwaarden.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="weeztix_oauth_token",
    )

    encrypted_access_token = models.TextField()

    encrypted_refresh_token = models.TextField(
        blank=True,
        default="",
    )

    token_type = models.CharField(
        max_length=50,
        default="Bearer",
    )

    scope = models.TextField(
        blank=True,
        default="",
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    refresh_token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Weeztix OAuth-token"
        verbose_name_plural = "Weeztix OAuth-tokens"

    def __str__(self) -> str:
        return f"Weeztix OAuth-token voor gebruiker {self.user_id}"