import os
import re

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Profile

ALLOWED_AVATAR_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB


def validate_avatar_file(avatar_file):
    if not avatar_file:
        return
    ext = os.path.splitext(avatar_file.name)[1].lower()
    if ext not in ALLOWED_AVATAR_EXTENSIONS:
        raise ValidationError('Avatar must be JPG, PNG, or WEBP.')
    if avatar_file.size > MAX_AVATAR_SIZE:
        raise ValidationError('Avatar file size must not exceed 2 MB.')


class LoginForm(forms.Form):
    login = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'login',
            'placeholder': 'Enter your login here',
            'autocomplete': 'username',
        }),
    )
    password = forms.CharField(
        max_length=128,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password',
            'placeholder': 'Enter your password here',
            'autocomplete': 'current-password',
        }),
    )
    next = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean_next(self):
        next_url = self.cleaned_data.get('next', '').strip()
        if not next_url:
            return ''
        allowed_hosts = {self.request.get_host()} if self.request else None
        if url_has_allowed_host_and_scheme(url=next_url, allowed_hosts=allowed_hosts):
            return next_url
        return ''

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('login', '').strip()
        password = cleaned_data.get('password', '')

        if username and password:
            user = authenticate(self.request, username=username, password=password)
            if user is None:
                raise ValidationError('Sorry, wrong login or password!')
            if not user.is_active:
                raise ValidationError('This user account is inactive.')
            self.user = user

        return cleaned_data


class SignupForm(forms.Form):
    login = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'login',
            'autocomplete': 'username',
        }),
    )
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'email',
            'autocomplete': 'email',
        }),
    )
    nickname = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'nickname',
        }),
    )
    password = forms.CharField(
        min_length=8,
        max_length=128,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password',
            'autocomplete': 'new-password',
        }),
    )
    password2 = forms.CharField(
        min_length=8,
        max_length=128,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password2',
            'autocomplete': 'new-password',
        }),
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'id': 'avatar',
            'accept': 'image/png, image/jpeg, image/webp',
        }),
    )

    def clean_login(self):
        username = self.cleaned_data.get('login', '').strip()
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError('Login can only contain Latin letters, digits, and underscores.')
        if User.objects.filter(username=username).exists():
            raise ValidationError('This login is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Sorry, this email address is already registered!')
        return email

    def clean_nickname(self):
        return self.cleaned_data.get('nickname', '').strip()

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            validate_avatar_file(avatar)
        return avatar

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('password2')
        username = cleaned_data.get('login')
        email = cleaned_data.get('email')

        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Passwords do not match.')

        if p1:
            dummy_user = User(username=username, email=email)
            try:
                validate_password(p1, user=dummy_user)
            except ValidationError as error:
                self.add_error('password', error)

        return cleaned_data

    def save(self):
        username = self.cleaned_data['login']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        nickname = self.cleaned_data['nickname']
        avatar = self.cleaned_data.get('avatar')

        user = User.objects.create_user(username=username, email=email, password=password)
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.nickname = nickname
        if avatar:
            profile.avatar = avatar
        profile.save()

        return user


class ProfileEditForm(forms.Form):
    login = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'login',
            'autocomplete': 'username',
        }),
    )
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'email',
            'autocomplete': 'email',
        }),
    )
    nickname = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'nickname',
        }),
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'id': 'avatar',
            'accept': 'image/png, image/jpeg, image/webp',
        }),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        if user and 'initial' not in kwargs:
            profile = getattr(user, 'profile', None)
            kwargs['initial'] = {
                'login': user.username,
                'email': user.email,
                'nickname': profile.nickname if profile else '',
            }
        super().__init__(*args, **kwargs)

    def clean_login(self):
        username = self.cleaned_data.get('login', '').strip()
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError('Login can only contain Latin letters, digits, and underscores.')
        if self.user and User.objects.filter(username=username).exclude(pk=self.user.pk).exists():
            raise ValidationError('This login is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if self.user and User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise ValidationError('Sorry, this email address is already registered!')
        return email

    def clean_nickname(self):
        return self.cleaned_data.get('nickname', '').strip()

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            validate_avatar_file(avatar)
        return avatar

    def save(self):
        self.user.username = self.cleaned_data['login']
        self.user.email = self.cleaned_data['email']
        self.user.save()

        profile, _ = Profile.objects.get_or_create(user=self.user)
        profile.nickname = self.cleaned_data['nickname']
        if self.cleaned_data.get('avatar'):
            profile.avatar = self.cleaned_data['avatar']
        profile.save()

        return self.user
