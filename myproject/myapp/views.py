# Встроенные библиотеки Django
from django.shortcuts import render, redirect  # Встроенная библиотека Django для рендеринга шаблонов и перенаправлений
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm  # Встроенные формы Django для создания пользователей и аутентификации
from django.contrib.auth import login, logout, authenticate  # Встроенные функции Django для управления аутентификацией
from django.contrib.auth.decorators import login_required  # Встроенный декоратор Django для проверки аутентификации пользователя
from django.contrib import messages  # Встроенная библиотека Django для отображения сообщений пользователю
from django.contrib.auth.models import User as DjangoUser  # Встроенная модель пользователя Django
import random # подключение рандома 

# Внешние библиотеки Django
from .forms import PostForm, RegistrationForm, CustomLoginForm  # Пользовательские формы, определенные в приложении
from django.core.files.storage import default_storage  # Встроенная библиотека Django для управления хранилищем файлов
from django.core.files.base import ContentFile  # Встроенная библиотека Django для работы с файлами
from django.http import JsonResponse  # Встроенная библиотека Django для создания JSON-ответов

# Внутренние модели приложения
from .models import User, Post, Like, Comment  # Пользовательские модели, определенные в приложении

# ООП: Использование декоратора для проверки аутентификации пользователя
@login_required
def create_post(request):
    if request.method == 'POST':
        # Cоздается объект формы PostForm и использует его методы для валидации данных и сохранения поста.
        form = PostForm(request.POST, request.FILES)  # Инициализация формы с данными из POST-запроса и файлами
        if form.is_valid():  # Проверка валидности формы
            image = form.cleaned_data['image']  # Получение очищенных данных из формы
            text = form.cleaned_data['text']
            user_id = str(request.user)  # Получение ID текущего пользователя

            # Сохранение файла в локальную папку
            file_path = default_storage.save(f'media/posts/{image.name}', ContentFile(image.read()))
            image_url = request.build_absolute_uri(default_storage.url(file_path))  # Построение абсолютного URL для файла

            # ООП: Вызов метода класса для создания поста
            Post.create_post(image_url, text, user_id)

            return redirect('post_list')  # Перенаправление на страницу со списком постов
    else:
        form = PostForm()  # Инициализация пустой формы
    return render(request, 'create_post.html', {'form': form})  # Рендеринг шаблона с формой

def my_view(request):
    if request.user.is_authenticated:
        username = request.user.username
    else:
        username = 'Login'
    return render(request, 'my_template.html', {'username': username})

def generate_random_color():
    return '#{:06x}'.format(random.randint(0, 0xFFFFFF))

def post_list(request):
    # ООП: Вызов метода класса для получения всех постов
    username = ''
    if request.user.is_authenticated:
        user_data = User.get_user_by_id(request.user)
        username = user_data.get('nickname', '')
    posts = Post.get_all_posts()
    return render(request, 'post_list.html', {'posts': posts, 'username': username})  # Рендеринг шаблона со списком постов


def post_detail(request, pk):
    # ООП: Вызов метода класса для получения поста по ID
    post = Post.get_post_by_id(pk)
    user = User.get_user_by_id(post['user_id']) if post else None  # Получение пользователя, создавшего пост
    like_count = Like.get_like_count(pk)  # Получение количества лайков для поста
    user_id = str(request.user) if request.user.is_authenticated else None  # Получение ID текущего пользователя
    print(f"User ID: {user_id}")
    user_liked = Like.is_liked_by_user(user_id, pk) if user_id else False  # Проверка, лайкнул ли текущий пользователь пост
    username = ''
    if request.user.is_authenticated:
        user_data = User.get_user_by_id(request.user)
        username = user_data.get('nickname', '')
    comments = Comment.get_comments_by_post(pk)  # Получение комментариев для поста
    
    context = {
        'post': post,
        'username': username,
        'user': user,
        'like_count': like_count,
        'user_liked': user_liked,
        'comments': comments,
    }
    return render(request, 'post_detail.html', context)  # Рендеринг шаблона с деталями поста


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)  # Инициализация формы с данными из POST-запроса
        if form.is_valid():  # Проверка валидности формы
            user = form.save()  # Сохранение пользователя

            # Проверка существования пользователя в Supabase
            existing_user = User.get_user_by_login(user.username)
            if existing_user:
                
                messages.error(request, 'User with this username already exists in Supabase.')  # Отображение сообщения об ошибке
                return redirect('register')  # Перенаправление на страницу регистрации

            # ООП: Вызов метода класса для создания пользователя
            User.create_user(user.username, form.cleaned_data['password1'], form.cleaned_data['nickname'])

            # Если данные правильные, найдите или создайте пользователя в Django
            django_user, created = DjangoUser.objects.get_or_create(username=user.username)

            if created:
                django_user.set_password(form.cleaned_data['password1'])  # Установка пароля для нового пользователя
                django_user.save()  # Сохранение пользователя
            login(request, django_user)  # Вход пользователя
            return redirect('login')  # Перенаправление на страницу со списком постов
    else:
        form = RegistrationForm()  # Инициализация пустой формы
    return render(request, 'register.html', {'form': form})  # Рендеринг шаблона с формой регистрации

def user_login(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)  # Инициализация формы с данными из POST-запроса
        if form.is_valid():  # Проверка валидности формы
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            # Проверка данных пользователя в Supabase
            user_data = User.get_user_by_login(username)
            if user_data:
               
                
                # Если данные правильные, найдите или создайте пользователя в Django
                django_user, created = DjangoUser.objects.get_or_create(username=user_data['id'])

                if created:
                    django_user.set_password(password)  # Установка пароля для нового пользователя
                    django_user.save()  # Сохранение пользователя
                login(request, django_user)  # Вход пользователя
                return redirect('post_list')  # Перенаправление на страницу со списком постов
            else:
                messages.error(request, 'Invalid login credentials.')  # Отображение сообщения об ошибке
                return redirect('login')  # Перенаправление на страницу входа
    else:
        form = CustomLoginForm()  # Инициализация пустой формы
    return render(request, 'login.html', {'form': form})  # Рендеринг шаблона с формой входа

def user_logout(request):
    logout(request)  # Выход пользователя
    return redirect('post_list')  # Перенаправление на страницу со списком постов

# ООП: Использование декоратора для проверки аутентификации пользователя
@login_required
def account(request):
    # Получите ID пользователя из request.user
    user_id = request.user

    # ООП: Вызов метода класса для получения данных пользователя по ID
    user_data = User.get_user_by_id(user_id)

    context = {
        'user_data': user_data,
    }
    return render(request, 'account.html', context)  # Рендеринг шаблона с данными пользователя

# ООП: Использование декоратора для проверки аутентификации пользователя
@login_required
def toggle_like(request, pk):
    if request.method == 'POST':
        user_id = str(request.user)  # Получение ID текущего пользователя
        post_id = str(pk)  # Получение ID поста
        # ООП: Вызов метода класса для переключения лайка
        Like.toggle_like(user_id, post_id)
        return redirect('post_detail', pk=post_id)  # Перенаправление на страницу с деталями поста
    return redirect('post_detail', pk=pk)
# ООП: Использование декоратора для проверки аутентификации пользователя
@login_required
def add_comment(request, pk):
    print('request')
    if request.method == 'POST':
        text = request.POST.get('text')  # Получение текста комментария из POST-запроса
        print(text)
        user_id = str(request.user)  # Получение ID текущего пользователя
        post_id = str(pk)  # Получение ID поста
        # ООП: Вызов метода класса для добавления комментария
        Comment.add_comment(text, user_id, post_id)
        return redirect('post_detail', pk=post_id)  # Возврат JSON-ответа
    return JsonResponse({'error': 'Invalid request method'}, status=400)  # Возврат ошибки для неправильного метода запроса
