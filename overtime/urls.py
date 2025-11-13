from django.urls import path
from overtime import views


urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('teams/create/', views.create_team, name='create_team'),
    path('signout/', views.signout, name='signout'),
    path('teams/<uuid:team_id>/set-wake/', views.set_wake_time, name='set_wake_time'),
    path('teams/join/', views.join_team, name='join_team'),
]