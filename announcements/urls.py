from django.urls import path
from . import views

app_name = 'announcements' # e.g., app_name = 'groups'

urlpatterns = [
    path('', views.announcement_list, name='list'),
    path('create/', views.create_announcement, name='create_announcement'),
    path('<int:announcement_id>/delete/', views.delete_announcement, name='delete_announcement'),
]