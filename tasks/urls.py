from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # --- MENTOR / COORDINATOR ACTIONS ---
    # Logic to create a task and distribute it to a group
    path('initialize/', views.initialize_task, name='initialize_task'),
    
    # Global board for Coordinators to see completion stats of all tasks
    path('manager/', views.global_task_manager, name='task_manager'),
    
    # Mentor's private inbox of pending submissions (Oldest First)
    path('review-queue/', views.review_queue, name='review_queue'),
    
    # The split-screen grading suite for a specific submission
    path('submission/<int:submission_id>/review/', views.review_submission, name='review_submission'),


    # --- MENTEE ACTIONS ---
    # Full-screen repository of all tasks for a specific mentee
    path('my-tasks/', views.my_tasks_list, name='my_tasks_list'),
    
    # Detail view (Instructions + Resource links + Version history)
    path('assignment/<int:assignment_id>/', views.task_detail, name='task_detail'),
    
    # Logic to process the OneDrive link and create a new Version
    path('assignment/<int:assignment_id>/submit/', views.submit_work, name='submit_work'),
]