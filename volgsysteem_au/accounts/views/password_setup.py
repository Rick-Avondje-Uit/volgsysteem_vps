from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.http import urlsafe_base64_decode

User = get_user_model()

def set_username_password(request, uidb64=None, token=None):
    if uidb64 is None or token is None:
        return HttpResponse("Ongeldige link.")

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                user.username = user.email
                form.save()
                user.is_active = True
                user.save()
                return HttpResponse("Je gebruikersnaam en wachtwoord zijn ingesteld. Je kunt nu inloggen.")
        else:
            form = SetPasswordForm(user)
        return render(request, 'registration/set_username_password.html', {'form': form})
    else:
        return HttpResponse("De link is ongeldig of verlopen.")