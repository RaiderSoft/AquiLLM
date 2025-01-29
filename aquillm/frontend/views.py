from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def folder_app(request):
    return render(request, 'frontend/index.html') 