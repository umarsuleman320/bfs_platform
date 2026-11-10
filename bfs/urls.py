"""
URL configuration for bfs project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
from accounts.views import BFSLoginView, RegisterView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', BFSLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('accounts/', include('accounts.urls')),
    path('groups/', include('groups.urls')),
    path('tasks/', include('tasks.urls')),
    path('progress/', include('progress.urls')),
    path('helpdesk/', include('helpdesk.urls')),
    path('notifications/', include('notifications.urls')),
    path('announcements/', include('announcements.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('', include('core.urls')), # This makes the core app the homepage
]
