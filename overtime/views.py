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

    # create a dict to hold timezone info for selector options. Then pass to template.
    zones_byGMT = {'GMT+0': 0, 'GMT+1': 1, 'GMT+2': 2,
             'GMT+3': 3, 'GMT+4': 4, 'GMT+5': 5,
             'GMT+6': 6, 'GMT+7': 7, 'GMT+8': 8,
             'GMT+9': 9, 'GMT+10': 10, 'GMT+11': 11,
             'GMT+12': 12, 'GMT-1': -1, 'GMT-2': -2,
             'GMT-3': -3, 'GMT-4': -4, 'GMT-5': -5,
             'GMT-6': -6, 'GMT-7': -7, 'GMT-8': -8,
             'GMT-9': -9, 'GMT-10': -10, 'GMT-11': -11,
             'GMT-12': -12}
    
    return render(request, 'dashboard.html', {'teams': teams, 'zones_byGMT': zones_byGMT})

