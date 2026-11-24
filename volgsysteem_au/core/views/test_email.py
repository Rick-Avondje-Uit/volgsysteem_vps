from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render
from core.forms import UserEmailForm

def test_send_email(request):
    if request.method == "POST":
        form = UserEmailForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]

            subject = "Test email volgsysteem 2.0"
            body = (
                "Hallo\n"
                "Als je dit leest werkt de mail functie naar behoren.\n"
                "Met vriendelijke groet Team Avondje Uit."
            )

            send_mail(
                subject,
                body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            return HttpResponse(
                "Email is als het goed is verzonden."
            )

    else:
        form = UserEmailForm()

    return render(
        request,
        "registration/test_email_form.html",
        {"form": form},
    )
