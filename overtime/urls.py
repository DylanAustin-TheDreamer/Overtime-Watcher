from django.urls import path
from overtime import views


urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('signout/', views.signout, name='signout'),
    path('contact/', views.contact, name='contact'),
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/join/', views.join_team, name='join_team'),
    path('update-time/', views.update_time, name='update_time'),
    path('export-data/', views.export_data, name='export_data'),
    path('teams/delete/<uuid:team_id>/', views.delete_group, name='delete_group'),
    path('teams/leave/<uuid:team_id>/', views.leave_group, name='leave_group'),
]