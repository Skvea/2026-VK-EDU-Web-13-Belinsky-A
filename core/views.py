from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.shortcuts import redirect, render


def login(request):
    if request.method == 'POST':
        username = request.POST.get('login', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('index')
        return render(request, 'core/login.html', {'has_error': True})
    return render(request, 'core/login.html')


def logout(request):
    auth_logout(request)
    return redirect('index')


def signup(request):
    return render(request, 'core/signup.html')


def profile(request):
    return render(request, 'core/profile.html')
