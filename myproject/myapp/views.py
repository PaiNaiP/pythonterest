from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User as DjangoUser
from .forms import PostForm, RegistrationForm, CustomLoginForm
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import JsonResponse
from .models import User, Post, Like, Comment

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
            Post.create_post(image_url, text, user_id)

            return redirect('post_list')
    else:
        form = PostForm()
    return render(request, 'create_post.html', {'form': form})

def post_list(request):
    posts = Post.get_all_posts()
    return render(request, 'post_list.html', {'posts': posts})

def post_detail(request, pk):
    post = Post.get_post_by_id(pk)
    user = User.get_user_by_id(post['user_id']) if post else None
    like_count = Like.get_like_count(pk)
    user_id = str(request.user)
    user_liked = Like.is_liked_by_user(user_id, pk)
    comments = Comment.get_comments_by_post(pk)

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
            user = form.save()

            # Проверка существования пользователя в Supabase
            existing_user = User.get_user_by_login(user.username)
            if existing_user:
                messages.error(request, 'User with this username already exists in Supabase.')
                return redirect('register')

            # Добавление нового пользователя в таблицу пользователей в Supabase
            User.create_user(user.username, form.cleaned_data['password1'], form.cleaned_data['nickname'])

            # Если данные правильные, найдите или создайте пользователя в Django
            django_user, created = DjangoUser.objects.get_or_create(username=user.username)

            if created:
                django_user.set_password(form.cleaned_data['password1'])
                django_user.save()
            login(request, django_user)
            return redirect('post_list')
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
            user_data = User.get_user_by_login(username)
            if user_data:
                # Если данные правильные, найдите или создайте пользователя в Django
                django_user, created = DjangoUser.objects.get_or_create(username=user_data['id'])

                if created:
                    django_user.set_password(password)
                    django_user.save()
                login(request, django_user)
                return redirect('post_list')
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
    user_data = User.get_user_by_id(user_id)

    context = {
        'user_data': user_data,
    }
    return render(request, 'account.html', context)

@login_required
def toggle_like(request, pk):
    if request.method == 'POST':
        user_id = str(request.user)
        post_id = str(pk)
        liked = Like.toggle_like(user_id, post_id)
        like_count = Like.get_like_count(post_id)
        return JsonResponse({'liked': liked, 'like_count': like_count})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def add_comment(request, pk):
    if request.method == 'POST':
        text = request.POST.get('text')
        user_id = str(request.user)
        post_id = str(pk)
        Comment.add_comment(text, user_id, post_id)
        comments = Comment.get_comments_by_post(post_id)
        return JsonResponse({'comments': comments})
    return JsonResponse({'error': 'Invalid request method'}, status=400)
