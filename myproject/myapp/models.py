# Встроенные библиотеки Django
from django.db import models  # Встроенная библиотека Django для определения моделей
from django.contrib.auth.hashers import make_password, check_password  # Встроенные функции Django для хеширования паролей
import uuid  # Встроенная библиотека Python для генерации UUID

# Внешние библиотеки
from .supabase_client import supabase  # Внешняя библиотека для взаимодействия с Supabase

# ООП: Определение класса User, наследующегося от models.Model
class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    login = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)
    nickname = models.CharField(max_length=50)

    # ООП: Метод класса для создания пользователя
    # Использование инкапсуляции, чтобы скрыть внутренние детали классов и предоставить интерфейсы для взаимодействия с ними
    # Абстракция: методы в классе User абстрагируют сложную логику работы с базой данных Supabase, предоставляя простые методы для вызова.
    @classmethod
    def create_user(cls, login, password, nickname):
        user_data = {
            'login': login,
            'password': password,
            'nickname': nickname,
        }
        response = supabase.table('user_table').insert(user_data).execute()
        return response.data[0] if response.data else None

    # ООП: Метод класса для получения пользователя по логину
    @classmethod
    def get_user_by_login(cls, login):
        response = supabase.table('user_table').select('*').eq('login', login).execute()
        return response.data[0] if response.data else None

    # ООП: Метод класса для получения пользователя по ID
    @classmethod
    def get_user_by_id(cls, user_id):
        response = supabase.table('user_table').select('*').eq('id', user_id).execute()
        return response.data[0] if response.data else None

# ООП: Определение класса Post, наследующегося от models.Model
class Post(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    image = models.TextField()
    text = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.text[:50]

    # ООП: Метод класса для создания поста
    # Полиморфизм: методы create_post, get_all_posts, и get_post_by_id в классе Post могут быть вызваны на объектах класса Post, несмотря на то, что они работают с разными данными.
    @classmethod
    def create_post(cls, image_url, text, user_id):
        post_data = {
            'image': image_url,
            'text': text,
            'user_id': user_id,
        }
        response = supabase.table('post_table').insert(post_data).execute()
        return response.data[0] if response.data else None

    # ООП: Метод класса для получения всех постов
    @classmethod
    def get_all_posts(cls):
        response = supabase.table('post_table').select('*').execute()
        return response.data

    # ООП: Метод класса для получения поста по ID
    @classmethod
    def get_post_by_id(cls, post_id):
        response = supabase.table('post_table').select('*').eq('id', post_id).execute()
        return response.data[0] if response.data else None

# ООП: Определение класса Like, наследующегося от models.Model
class Like(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    # ООП: Метод класса для переключения лайка
    @classmethod
    def toggle_like(cls, user_id, post_id):
        response = supabase.table('like_table').select('*').eq('user_id', user_id).eq('post_id', post_id).execute()
        if response.data:
            supabase.table('like_table').delete().eq('user_id', user_id).eq('post_id', post_id).execute()
            liked = False
        else:
            like_data = {
                'user_id': user_id,
                'post_id': post_id,
            }
            supabase.table('like_table').insert(like_data).execute()
            liked = True
        return liked

    # ООП: Метод класса для получения количества лайков
    @classmethod
    def get_like_count(cls, post_id):
        response = supabase.table('like_table').select('*').eq('post_id', post_id).execute()
        return len(response.data)

    # ООП: Метод класса для проверки, лайкнул ли пользователь пост
    @classmethod
    def is_liked_by_user(cls, user_id, post_id):
        response = supabase.table('like_table').select('*').eq('user_id', user_id).eq('post_id', post_id).execute()
        return bool(response.data)

# ООП: Определение класса Comment, наследующегося от models.Model
class Comment(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    text = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    # ООП: Метод класса для добавления комментария
    @classmethod
    def add_comment(cls, text, user_id, post_id):
        comment_data = {
            'text': text,
            'user_id': user_id,
            'post_id': post_id,
        }
        supabase.table('comment_table').insert(comment_data).execute()

    # ООП: Метод класса для получения комментариев поста
    @classmethod
    def get_comments_by_post(cls, post_id):
        response = supabase.table('comment_table').select('*').eq('post_id', post_id).execute()
        comments = response.data
        for comment in comments:
            user_response = supabase.table('user_table').select('*').eq('id', comment['user_id']).execute()
            comment['user'] = user_response.data[0] if user_response.data else None
        return comments