from django.test import TestCase, Client
from django.urls import reverse
from .models import User
from django.contrib.auth.models import User as DjangoUser

class RegistrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')

    def test_user_registration(self):
        data = {
            'username': 'testuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
            'nickname': 'Test User'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 302)  # Проверка перенаправления

        # Проверка создания пользователя в Supabase
        user_data = User.get_user_by_login('testuser')
        self.assertIsNotNone(user_data, "User should be created in Supabase")

        # Проверка создания пользователя в Django
        django_user = DjangoUser.objects.filter(username='testuser').first()
        self.assertIsNotNone(django_user, "User should be created in Django")

        # Проверка, что пользователь залогинен
        self.assertTrue(self.client.login(username='testuser', password='testpassword123'))
