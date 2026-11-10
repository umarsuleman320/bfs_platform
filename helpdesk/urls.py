from django.urls import path
from . import views

app_name = 'helpdesk'

urlpatterns = [
    path('', views.helpdesk_home, name='home'),
    path('new/', views.ticket_create, name='ticket_create'),
    path('<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('<int:ticket_id>/respond/', views.respond_ticket, name='respond_ticket'),
    path('<int:ticket_id>/status/', views.update_ticket_status, name='update_ticket_status'),
]