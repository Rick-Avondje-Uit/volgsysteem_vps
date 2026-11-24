from django import forms
from django.contrib.auth.models import User

class EmailLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class EmailRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Dit e-mailadres is al in gebruik.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email  # gebruik email als username
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

# accounts/forms.py
from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailOnlyPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="E-mailadres", max_length=254)

    def get_users(self, email):
        return User._default_manager.filter(email__iexact=email, is_active=True)
    

# accounts/forms.py
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailOnlyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email']  # username niet tonen

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email  # gebruik e-mail als username
        if commit:
            user.save()
        return user
    
class UserEmailForm(forms.Form):
    email = forms.EmailField(label='E-mailadres', max_length=254)