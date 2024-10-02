from django.urls import path
from . import views

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('post/<uuid:pk>/', views.post_detail, name='post_detail'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('account/', views.account, name='account'),
    path('create_post/', views.create_post, name='create_post'),
    path('post/<uuid:pk>/toggle_like/', views.toggle_like, name='toggle_like'),
]
