#coding=utf-8
__author__ = 'Administrator'
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from survey.models import UserProfile

class RegistrationForm(UserCreationForm):
    username = forms.CharField(max_length=30, min_length=3, label= 'Username')
    email = forms.EmailField(label="Email")
    password1 = forms.CharField(widget=forms.PasswordInput, min_length=5, label='Password' )
    password2 = forms.CharField(widget=forms.PasswordInput, min_length=5, label='Confirm password')

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class EditProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        try:
            # self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
        except User.DoesNotExist:
            pass

    # email = forms.EmailField()
    first_name  = forms.CharField(max_length=30, required=False)
    last_name  = forms.CharField(max_length=30, required=False)

    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name', 'contact_number', 'birth_date', 'im_name')

    def save(self, *args, **kw):
        super(EditProfileForm, self).save(*args, **kw)
        self.instance.user.first_name = self.cleaned_data.get('first_name')
        self.instance.user.last_name = self.cleaned_data.get('last_name')
        # self.instance.user.email = self.cleaned_data.get('email')
        self.instance.user.save()