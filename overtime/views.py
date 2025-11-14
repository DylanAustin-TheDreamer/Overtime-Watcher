from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse
from django.contrib import messages
import json
from zoneinfo import ZoneInfo
from django.apps import apps
from .models import Team

# Create your views here.
def home(request):
    """Home page view."""

    return render(request, 'home.html')

def contact(request):
    """Contact page view."""

    return render(request, 'contact.html')

def signout(request):
    """Sign out page view."""

    return render(request, 'signout.html')

@login_required
def update_time(request):
    """View to update user's timezone and wake time from dashboard form."""

    return render(request, 'dashboard.html')

@login_required
def create_team(request):
    """View to create a new team."""

    return render(request, 'dashboard.html')

@login_required
def join_team(request):
    """View to join a team using a join code."""

    return render(request, 'dashboard.html')
















# Works - Completed
@login_required
def dashboard(request):
    """Dashboard view showing user's teams and settings."""

    # Show teams the current user belongs to and their memberships
    if request.user.is_authenticated:
        teams = Team.objects.filter(memberships__user=request.user).distinct()
    return render(request, 'dashboard.html', {'teams': teams})

