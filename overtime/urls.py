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
]