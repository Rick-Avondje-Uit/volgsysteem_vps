from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from accounts.forms import EmailOnlyPasswordResetForm

class CustomPasswordResetView(PasswordResetView):
    form_class = EmailOnlyPasswordResetForm
    template_name = 'registration/password_reset_form.html'
    success_url = '/password_reset/done/'

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = SetPasswordForm
    template_name = 'registration/password_reset_confirm.html'

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'