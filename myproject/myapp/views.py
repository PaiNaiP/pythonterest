from django.shortcuts import render
from django.http import JsonResponse
from .supabase_client import supabase

def get_users(request):
    response = supabase.table('user_table').select('*').execute()
    users = response.data
    return render(request, 'users.html', {'users': users})

def create_user(request):
    if request.method == 'POST':
        data = request.POST
        response = supabase.table('user_table').insert(data).execute()
        return JsonResponse(response.data, safe=False)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_posts(request):
    response = supabase.table('post_table').select('*').execute()
    posts = response.data
    return render(request, 'posts.html', {'posts': posts})

def create_post(request):
    if request.method == 'POST':
        data = request.POST
        response = supabase.table('post_table').insert(data).execute()
        return JsonResponse(response.data, safe=False)
    return JsonResponse({'error': 'Invalid request method'}, status=400)
