from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    BFSLoginView, RegisterView, ProfileUpdateView,
    user_directory, add_mentor, add_mentee,
    promote_user, toggle_user_status, user_detail
)

app_name = 'accounts'

urlpatterns = [
    path('login/', BFSLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='accounts:login'), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileUpdateView.as_view(), name='profile'),
    
    # User Management (Coordinator & Management)
    path('users/', user_directory, name='user_directory'),
    path('users/add-mentor/', add_mentor, name='add_mentor'),
    path('users/add-mentee/', add_mentee, name='add_mentee'),
    path('users/<int:user_id>/promote/', promote_user, name='promote_user'),
    path('users/<int:user_id>/toggle/', toggle_user_status, name='toggle_user_status'),
    path('users/<int:user_id>/detail/', user_detail, name='user_detail'),
]