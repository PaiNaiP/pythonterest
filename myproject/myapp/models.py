from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import uuid

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    login = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)  # Увеличиваем длину для хранения хэшированного пароля
    nickname = models.CharField(max_length=50)

class Post(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    image = models.TextField()
    text = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.text[:50]

class Like(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

class Comment(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    text = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
