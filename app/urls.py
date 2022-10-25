"""tdts URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('main/', views.main, name='main'),
    path('main/timesheet/', views.TimesheetView.as_view(), name='timesheet'),
    path('main/todolist/', views.ToDoListView.as_view(), name='todolist'),
    path('main/todolist/delete/<pk>/', views.deleteToDoListEntry, name='deleteToDoListEntry'),
    path('main/todolist/update/<pk>/', views.editToDoListEntry, name='editToDoListEntry'),
    # path('accounts/', include('django.contrib.auth.urls')),
    path('password_reset/', views.password_reset_request, name="password_reset"),
    path('admin/', admin.site.urls),
]
