from django.urls import path
from overtime import views


urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('signout/', views.signout, name='signout'),
    path('contact/', views.contact, name='contact'),
    path('confirm_delete/', views.confirm_delete, name='confirm_delete'),
    path('account_deleted_confirmation/', views.account_deleted_confirmation, name='account_deleted_confirmation'),
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/join/', views.join_team, name='join_team'),
    path('update-time/', views.update_time, name='update_time'),
    path('teams/delete/<uuid:team_id>/', views.delete_group, name='delete_group'),
    path('teams/leave/<uuid:team_id>/', views.leave_group, name='leave_group'),
    path('account/delete/', views.delete_account, name='delete_account'),
]