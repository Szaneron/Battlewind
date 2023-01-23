from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.forms import ModelForm

from .models import *


class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    widgets = {
        'email': forms.TextInput(attrs={'required': True})
    }


class EditUserProfileSettingsForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['summonerName', 'profilePic']

        widgets = {
            'summonerName': forms.TextInput(attrs={'class': 'form-control'}),
            'profilePic': forms.FileInput(attrs={'class': 'form-control', 'label': ''})
        }


class MyPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget = forms.PasswordInput(attrs={"class": "form-control", 'label': ''})
        self.fields["new_password1"].widget = forms.PasswordInput(attrs={"class": "form-control", 'label': ''})
        self.fields["new_password2"].widget = forms.PasswordInput(attrs={"class": "form-control", 'label': ''})
        # other customization


class CreateTeamForm(ModelForm):
    class Meta:
        model = Team
        fields = ['teamName']


class UploadImageToVeryficate(ModelForm):
    class Meta:
        model = Match
        fields = ['afterGameImage']

        widgets = {
            'afterGameImage': forms.FileInput(attrs={'class': 'form-control', 'label': '', 'required': True})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['afterGameImage'].label = ''
