from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from django import forms
from .models import *


class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class EditUserProfileSettingsForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['summonerName', 'profilePic']

        widgets = {
            'summonerName': forms.TextInput(attrs={'class': 'form-control'})
        }


class CreateTeamForm(ModelForm):
    class Meta:
        model = Team
        fields = ['teamName']


class UploadImageToVeryficate(ModelForm):
    class Meta:
        model = Match
        fields = ['afterGameImage']

        widgets = {
            'afterGameImage': forms.FileInput(attrs={'class': 'form-control', 'label': ''})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['afterGameImage'].label = ''