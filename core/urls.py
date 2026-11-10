from django.urls import path
from . import views

app_name = 'core' # e.g., app_name = 'groups'

urlpatterns = [
    path('', views.home, name='home'),
    path('wall-of-fame/', views.wall_of_fame, name='wall_of_fame'),
    path('wall-of-fame/manage/', views.manage_wall_of_fame, name='manage_wall_of_fame'),
    path('search/', views.global_search, name='search'),
]