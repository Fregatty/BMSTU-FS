# -*- coding: utf-8 -*-
from django import forms
from django .core import validators
from django.core.exceptions import ValidationError

from .models import UserFile, Folder
from django.forms import ModelForm
from django.contrib.auth.models import User
from .models import EducationalDepartment, Profile


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class UserRegistrationForm(forms.ModelForm):
    department_choice = []
    for f in EducationalDepartment.objects.all():
        tup = (f.id, f.name)
        department_choice.append(tup)
    department_choice.append((None, '-'))
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)
    department = forms.ChoiceField(label='Department', choices=department_choice)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email')

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']


class FileForm(forms.ModelForm):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True, 'directory': True}),
        label='Select a file',
    )

    def clean_file(self):
        file = self.cleaned_data.get('file', False)
        if file:
            if file.size > 10485760:
                raise forms.ValidationError("File is too large ( > 10mb )")
            return file
        else:
            raise forms.ValidationError("Couldn't read uploaded file")

    class Meta:
        model = UserFile
        fields = ('file',)


class FolderForm(forms.ModelForm):

    class Meta:
        model = Folder
        fields = ('name',)


class EmailForm(forms.Form):
    subject = forms.CharField(label='Subject', max_length=50)
    body = forms.CharField(label='Body', required=False, widget=forms.Textarea)
    to = forms.EmailField()

