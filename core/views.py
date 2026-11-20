from urllib.parse import urlparse

from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import LoginForm, ProfileEditForm, SignupForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    next_url = request.GET.get('next') or request.POST.get('next') or ''
    if request.method == 'POST':
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            auth_login(request, form.user)
            redirect_to = form.cleaned_data.get('next')
            if redirect_to and url_has_allowed_host_and_scheme(redirect_to, allowed_hosts={request.get_host()}):
                return redirect(redirect_to)
            return redirect('index')
    else:
        form = LoginForm(request=request, initial={'next': next_url})

    return render(request, 'core/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    auth_logout(request)
    referer = request.META.get('HTTP_REFERER')
    if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()}):
        parsed = urlparse(referer)
        target = parsed.path
        if parsed.query:
            target += f'?{parsed.query}'
        return redirect(target or '/')
    return redirect('index')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('index')
    else:
        form = SignupForm()

    return render(request, 'core/signup.html', {'form': form})


@login_required(login_url='login')
def profile_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            return render(request, 'core/profile.html', {'form': form, 'saved': True})
    else:
        form = ProfileEditForm(user=request.user)

    return render(request, 'core/profile.html', {'form': form})

login = login_view
logout = logout_view
signup = signup_view
profile = profile_view
