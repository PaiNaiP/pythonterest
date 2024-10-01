from django import forms

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class PostForm(forms.Form):
    image = forms.ImageField(label='Image')
    text = forms.CharField(widget=forms.Textarea, required=False, label='Text')


class RegistrationForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter your username'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password'}))

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']