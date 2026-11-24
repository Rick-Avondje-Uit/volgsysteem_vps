from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import Group

User = get_user_model()

def create_user_without_password(email, *, is_active=True):
    user = User.objects.create_user(
        username=email,
        email=email,
    )

    user.set_unusable_password()
    user.is_active = is_active
    user.save()

    return user

def create_begeleider(email):
    if User.objects.filter(email=email).exists():
        raise ValueError(
            "Er bestaat al een gebruiker met dit e-mailadres"
        )
    user = create_user_without_password(
        email,
        is_active=False,
    )

    begeleider_group, _ = Group.objects.get_or_create(
        name='Begeleider'
    )

    user.groups.add(begeleider_group)

    return user

def send_password_setup_email(user, request):
    reset_form = PasswordResetForm(
        {"email": user.email}
    )

    if not reset_form.is_valid():
        return False