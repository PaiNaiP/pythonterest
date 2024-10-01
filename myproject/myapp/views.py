from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .supabase_client import supabase
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import PostForm
from uuid import uuid4
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .forms import RegistrationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login
import os

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            text = form.cleaned_data['text']
            user_id = str(request.user)

            # Сохранение файла в локальную папку
            file_path = default_storage.save(f'media/posts/{image.name}', ContentFile(image.read()))
            image_url = request.build_absolute_uri(default_storage.url(file_path))

            # Создание нового поста в Supabase
            post_data = {
                'image': image_url,
                'text': text,
                'user_id': user_id,
            }
            response = supabase.table('post_table').insert(post_data).execute()
            # if response.status_code != 201:
            #     messages.error(request, f"Error creating post in Supabase: {response.text}")
            #     return redirect('create_post')

            return redirect('post_list')
    else:
        form = PostForm()
    return render(request, 'create_post.html', {'form': form})

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
        form = RegistrationForm(request.POST)
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
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Проверка данных пользователя в Supabase
            response = supabase.table('user_table').select('*').eq('login', username).eq('password', password).execute()
            if response.data:
                # Если данные правильные, найдите или создайте пользователя в Django
                user, created = User.objects.get_or_create(username=response.data[0]['id'])

                if created:
                    user.set_password(password)
                    user.save()
                login(request, user)
                return redirect('post_list')
            else:
                messages.error(request, 'Invalid login credentials.')
                return redirect('login')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('post_list')

@login_required
def account(request):
    print(request.user)
    return render(request, 'account.html')
