from django.urls import path
from overtime import views


urlpatterns = [
    path('', views.home, name='home'),
]