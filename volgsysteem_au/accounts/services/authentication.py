from django.contrib.auth import authenticate,get_user_model

User = get_user_model()

def authenticate_with_email(email,password):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return None

    return authenticate(
        username=user.username,
        password=password,
    )