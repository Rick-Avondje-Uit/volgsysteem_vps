from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import (
    login_required,
    user_passes_test,
)
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic.edit import CreateView
from accounts.forms import (
    EmailOnlyUserCreationForm,
    UserEmailForm,
)
from accounts.services import create_begeleider, create_user_without_password, send_password_setup_email

User = get_user_model()

def is_begeleider_or_admin(user):
    return (
        user.groups.filter(name='Begeleider').exists()
        or user.is_superuser
    )

@login_required
@user_passes_test(lambda u: u.groups.filter(name='Begeleider').exists())
def begeleider_create_user(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            create_user_without_password(email)
            return redirect('successpagina')

class CreateUserByEmailView(CreateView):
    model = User
    form_class = EmailOnlyUserCreationForm
    template_name = 'accounts/create_user.html'
    success_url = '/accounts/user-created/'

@login_required
@user_passes_test(is_begeleider_or_admin)
def create_begeleider_and_send_email(request):
    if request.method == 'POST':
        form = UserEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            try:
                user = create_begeleider(email)
            except ValueError as error:
                return HttpResponse(str(error))

            send_password_setup_email(
                user=user,
                request=request,
            )

            return HttpResponse(
               "E-mail verzonden om wachtwoord in te stellen."
           )

    else:
        form = UserEmailForm()

    return render(request, 'accounts/email_form.html', {'form': form})
