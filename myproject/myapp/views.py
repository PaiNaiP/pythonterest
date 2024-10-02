from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .supabase_client import supabase
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import PostForm
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .forms import RegistrationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomLoginForm
import os
from django.http import JsonResponse
from .models import User  # Импортируем вашу модель User
from django.contrib.auth.hashers import make_password
from .models import User as CustomUser  # Импортируем вашу модель User
from django.contrib.auth.models import User as DjangoUser


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

    # Получите информацию о пользователе, который загрузил пост
    user_response = supabase.table('user_table').select('*').eq('id', post['user_id']).execute()
    user = user_response.data[0] if user_response.data else None

    # Получите количество лайков для поста
    like_response = supabase.table('like_table').select('*').eq('post_id', pk).execute()
    like_count = len(like_response.data)

    # Получите состояние лайка для текущего пользователя
    user_id = str(request.user)
    user_like_response = supabase.table('like_table').select('*').eq('user_id', user_id).eq('post_id', pk).execute()
    user_liked = bool(user_like_response.data)

    # Получите комментарии для поста
    comments_response = supabase.table('comment_table').select('*').eq('post_id', pk).execute()
    comments = comments_response.data

    # Получите информацию о пользователях, которые оставили комментарии
    for comment in comments:
        user_response = supabase.table('user_table').select('*').eq('id', comment['user_id']).execute()
        comment['user'] = user_response.data[0] if user_response.data else None

    context = {
        'post': post,
        'user': user,
        'like_count': like_count,
        'user_liked': user_liked,
        'comments': comments,
    }
    return render(request, 'post_detail.html', context)

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Хэширование пароля
            raw_password = form.cleaned_data['password1']
            hashed_password = make_password(raw_password)

            # Добавление нового пользователя в таблицу пользователей в Supabase
            supabase_user_data = {
                'login': form.cleaned_data['username'],
                'password': hashed_password,
                'nickname': form.cleaned_data['nickname'],
            }
            response = supabase.table('user_table').insert(supabase_user_data).execute()
            if response.data:
                # Получение ID пользователя из Supabase
                user_id = response.data[0]['id']

                # Создание пользователя в Django
                custom_user = CustomUser(
                    id=user_id,
                    login=form.cleaned_data['username'],
                    password=hashed_password,
                    nickname=form.cleaned_data['nickname']
                )
                custom_user.save()

                # Создание пользователя в Django для аутентификации
                django_user = DjangoUser.objects.create_user(
                    username=response.data[0]['id'],
                    password=raw_password
                )

                login(request, django_user)
                return redirect('post_list')
            else:
                messages.error(request, 'Error creating user in Supabase.')
                return redirect('register')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Проверка данных пользователя в Supabase
            response = supabase.table('user_table').select('*').eq('login', username).execute()
            if response.data:
                user_data = response.data[0]
                # Создаем экземпляр модели User для использования метода check_password
                custom_user = CustomUser(login=user_data['login'], password=user_data['password'], nickname=user_data['nickname'])
                if custom_user.check_password(password):
                    # Если данные правильные, найдите или создайте пользователя в Django
                    django_user, created = DjangoUser.objects.get_or_create(username=response.data[0]['id'])

                    if created:
                        django_user.set_password(password)
                        django_user.save()
                    login(request, django_user)
                    return redirect('post_list')
                else:
                    messages.error(request, 'Invalid login credentials.')
                    return redirect('login')
            else:
                messages.error(request, 'Invalid login credentials.')
                return redirect('login')
    else:
        form = CustomLoginForm()
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('post_list')

@login_required
def account(request):
    # Получите ID пользователя из request.user
    user_id = request.user

    # Получите данные пользователя из Supabase
    response = supabase.table('user_table').select('*').eq('id', user_id).execute()
    user_data = response.data[0] if response.data else None

    context = {
        'user_data': user_data,
    }
    return render(request, 'account.html', context)

@login_required
def toggle_like(request, pk):
    if request.method == 'POST':
        user_id = str(request.user)
        post_id = str(pk)
        # Проверка, существует ли лайк
        response = supabase.table('like_table').select('*').eq('user_id', user_id).eq('post_id', post_id).execute()
        if response.data:
            # Если лайк существует, удалите его
            supabase.table('like_table').delete().eq('user_id', user_id).eq('post_id', post_id).execute()
            liked = False
        else:
            # Если лайка нет, добавьте его
            like_data = {
                'user_id': user_id,
                'post_id': post_id,
            }
            supabase.table('like_table').insert(like_data).execute()
            liked = True

        # Получите обновленное количество лайков
        like_response = supabase.table('like_table').select('*').eq('post_id', post_id).execute()
        like_count = len(like_response.data)

        return JsonResponse({'liked': liked, 'like_count': like_count})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def add_comment(request, pk):
    if request.method == 'POST':
        text = request.POST.get('text')
        user_id = str(request.user)
        post_id = str(pk)

        # Добавление нового комментария в Supabase
        comment_data = {
            'text': text,
            'user_id': user_id,
            'post_id': post_id,
        }
        supabase.table('comment_table').insert(comment_data).execute()

        # Получение обновленного списка комментариев
        comments_response = supabase.table('comment_table').select('*').eq('post_id', post_id).execute()
        comments = comments_response.data

        # Получение информации о пользователях, которые оставили комментарии
        for comment in comments:
            user_response = supabase.table('user_table').select('*').eq('id', comment['user_id']).execute()
            comment['user'] = user_response.data[0] if user_response.data else None

        return JsonResponse({'comments': comments})
    return JsonResponse({'error': 'Invalid request method'}, status=400)
