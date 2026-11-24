from django.shortcuts import render, redirect
from django.contrib.auth import login
from accounts.forms import EmailLoginForm
from accounts.services.authentication import authenticate_with_email


def login_view(request):
    form = EmailLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate_with_email(
            form.cleaned_data['email'],
            form.cleaned_data['password']
        )
        if user:
            login(request, user)
            return redirect('core:index')
        else:
            form.add_error(None, "Ongeldig e-mailadres of wachtwoord.")
    return render(request, 'accounts/login.html', {'form': form})
