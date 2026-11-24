from django.contrib.auth.views import LogoutView
from django.urls import path
from accounts.views import  login_view, CustomPasswordResetView, CustomPasswordResetDoneView, CustomPasswordResetConfirmView, CustomPasswordResetCompleteView

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page="/"), name='logout'),
    # URL voor het aanvragen van een wachtwoord reset
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),

    # URL voor het bevestigen van de aanvraag
    path('password_reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),

    # URL voor het resetten van het wachtwoord (deze bevat een unieke sleutel)
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # URL die aangeeft dat het wachtwoord resetten succesvol is afgerond
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]