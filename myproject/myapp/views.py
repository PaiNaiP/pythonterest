from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .supabase_client import supabase
from django.contrib import messages

def post_list(request):
    # Получите все посты из Supabase
    response = supabase.table('post_table').select('*').execute()
    posts = response.data
    return render(request, 'post_list.html', {'posts': posts})

def post_detail(request, pk):
    # Получите один пост из Supabase по его ID
    response = supabase.table('post_table').select('*').eq('id', pk).execute()
    post = response.data[0] if response.data else None
    return render(request, 'post_detail.html', {'post': post})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Проверка существования пользователя в Supabase
            response = supabase.table('user_table').select('*').eq('login', user.username).execute()
            if response.data:
                messages.error(request, 'User with this username already exists in Supabase.')
                return redirect('register')

            # Добавление нового пользователя в таблицу пользователей в Supabase
            supabase_user_data = {
                'login': user.username,
                'password': form.cleaned_data['password1'],
                'nickname': user.username,
            }
            response = supabase.table('user_table').insert(supabase_user_data).execute()
            if response.status_code != 201:
                messages.error(request, f"Error creating user in Supabase: {response.text}")
                return redirect('register')

            login(request, user)
            return redirect('post_list')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('post_list')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('post_list')

@login_required
def account(request):
    return render(request, 'account.html')
