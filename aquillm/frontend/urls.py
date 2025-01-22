from django.urls import path
from . import views

urlpatterns = [
    path('folders/', views.folder_app, name='folder_app'),
] 