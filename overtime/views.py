from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_datetime
from zoneinfo import ZoneInfo
from overtime.models import Team, Profile
from datetime import timedelta, datetime
from django.utils import timezone

# Create your views here.
def home(request):
    """Home page view."""

    return render(request, 'home.html')

def contact(request):
    """Contact page view."""

    return render(request, 'contact.html')

def signout(request):
    """Sign out page view."""

    return render(request, 'account/signout.html')








# works - Completed
@login_required
def delete_account(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        if request.user.check_password(password):
            user = request.user
            logout(request)
            user.delete()
            return redirect('account_deleted_confirmation')
        else:
            password_message = 'Incorrect password!'
    return render(request, 'account/confirm_delete.html', {'password_message': password_message})

def confirm_delete(request):
    return render(request, 'account/confirm_delete.html')

def account_deleted_confirmation(request):
    return render(request, 'account/account_deleted_confirmation.html')

# works - Completed
@login_required
def update_time(request):
    if request.method == 'POST':
        profile, created = Profile.objects.get_or_create(user=request.user)
        timezone_val = request.POST.get('timezone')
        wake_time_val = request.POST.get('wake_time')
        
        if timezone_val:
            # Convert number to GMT format: "5" -> "GMT+5", "-3" -> "GMT-3"
            tz_num = int(timezone_val)
            profile.timezone = f"GMT{'+' if tz_num >= 0 else ''}{tz_num}"
        if wake_time_val:
            # Convert "HH:MM" string to time object for TimeField
            profile.wake_time = datetime.strptime(wake_time_val, "%H:%M").time()
        
        profile.save()
    
    return redirect('dashboard')

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
    
    return render(request, 'dashboard.html', {'teams': teams, 'zones_byGMT': zones_byGMT,})

# works - Completed
@login_required
def create_team(request):
    """View to create a new team."""
    if request.method == 'POST':
        team_name = request.POST.get('name', '').strip()
        if team_name:
            team = Team.objects.create(
                name=team_name,
                created_by=request.user
            )
            team.members.add(request.user)
            team.save()
            return redirect('dashboard')
    return render(request, 'dashboard.html')

# works - Completed
@login_required
def join_team(request):
    """View to join a team using a join code."""

    if request.method == 'POST':
        join_code = request.POST.get('join_code', '').strip().upper()
        try:
            team = Team.objects.get(join_code=join_code)
            team.members.add(request.user)
            team.save()
            return redirect('dashboard')
        except Team.DoesNotExist:
            pass  # Optionally handle invalid join code here
    return render(request, 'dashboard.html')

# works - Completed
@login_required
def delete_group(request, team_id):
    """View to delete a team."""
    try:
        team = Team.objects.get(id=team_id, created_by=request.user)
        team.delete()
    except Team.DoesNotExist:
        pass  # Optionally handle the case where the team does not exist or user is not authorized
    return redirect('dashboard')

# works - Completed
@login_required
def leave_group(request, team_id):
    """View to leave a team."""
    try:
        team = Team.objects.get(id=team_id)
        team.members.remove(request.user)
        team.save()
    except Team.DoesNotExist:
        pass  # Optionally handle the case where the team does not exist
    return redirect('dashboard')