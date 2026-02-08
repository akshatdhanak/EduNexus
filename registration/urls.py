from django.urls import path, include

from . import views

app_name = 'registration'

urlpatterns = [
    path('', views.custom_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
]
