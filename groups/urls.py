from django.urls import path
from . import views

app_name = 'groups'

urlpatterns = [
    path('', views.group_list, name='group_list'),
    path('<int:group_id>/', views.group_detail, name='group_detail'),
    path('<int:group_id>/view/', views.mentee_group_view, name='mentee_group_view'),
    path('<int:group_id>/join/', views.request_to_join, name='request_to_join'),
    path('<int:group_id>/remove/<int:user_id>/', views.remove_member, name='remove_member'),
    path('<int:group_id>/add-members/', views.add_members_logic, name='add_members'),
    path('<int:group_id>/assign-mentor/', views.assign_mentor, name='assign_mentor'),
    path('request/<int:request_id>/approve/', views.approve_request, name='approve_request'),
    path('request/<int:request_id>/reject/', views.reject_request, name='reject_request'),
    path('create/', views.create_group, name='create_group'), 
    path('<int:group_id>/edit/', views.edit_group, name='edit_group'),
    path('<int:group_id>/archive/', views.archive_group, name='archive_group'),
    path('<int:group_id>/delete/', views.delete_group, name='delete_group'),

    # Pairings (1-to-1 & 1-to-Many)
    path('pairings/', views.pairing_list, name='pairing_list'),
    path('pairings/create/', views.create_pairing, name='create_pairing'),
    path('pairings/<int:pairing_id>/terminate/', views.terminate_pairing, name='terminate_pairing'),

    # Meetings & Requests
    path('meetings/', views.meeting_list, name='meeting_list'),
    path('meetings/schedule/', views.schedule_meeting, name='schedule_meeting'),
    path('meetings/request/', views.request_meeting, name='request_meeting'),
    path('meetings/requests/<int:request_id>/review/', views.review_meeting_request, name='review_meeting_request'),
    path('meetings/<int:meeting_id>/complete/', views.complete_meeting, name='complete_meeting'),
    path('meetings/<int:meeting_id>/cancel/', views.cancel_meeting, name='cancel_meeting'),
]