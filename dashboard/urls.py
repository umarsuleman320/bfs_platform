from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # The central entry point /dashboard/
    path('', views.dashboard_home, name='home'),
    
    # Role-specific terminals
    path('mentee/', views.mentee_dashboard, name='mentee_dashboard'),
    path('mentor/', views.mentor_dashboard, name='mentor_dashboard'),
    path('management/', views.management_dashboard, name='management_dashboard'),
    path('coordinator/', views.coordinator_dashboard, name='coordinator_dashboard'),
]