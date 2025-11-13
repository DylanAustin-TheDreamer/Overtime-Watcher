from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.http import JsonResponse
from django.contrib import messages
import json

# Create your views here.
def home(request):
    return render(request, 'home.html')

def contact(request):
    return render(request, 'contact.html')


def dashboard(request):
    # Show teams the current user belongs to and their memberships
    if request.user.is_authenticated:
        from .models import Team
        teams = Team.objects.filter(memberships__user=request.user).prefetch_related('memberships__user').distinct()
    else:
        teams = []
    return render(request, 'dashboard.html', { 'teams': teams })

@login_required
def join_team(request):
    """Handle dashboard team-joining form POST.
    Expects `join_code` in POST. Joins the Team if found.
    Redirects back to the dashboard.
    """
    from .models import Team

    if request.method != 'POST':
        return redirect('dashboard')

    join_code = (request.POST.get('join_code'))
    if not join_code:
        # nothing provided, just go back
        return redirect('dashboard')

    try:
        team = Team.objects.get(join_code=join_code)
    except Team.DoesNotExist:
        messages.error(request, 'No team found with that join code.')
        return redirect('dashboard')

    membership, created = team.add_member(request.user, is_admin=False)
    created = True
    membership.save()
    # Redirect with a small query hint so the dashboard can show the joined team even
    # if the messages framework isn't installed/visible.
    return redirect(f"{reverse('dashboard')}?joined={team.join_code}")

@login_required
def create_team(request):
    """Handle dashboard team-creation form POST.
    Expects `name` in POST. Creates a Team and adds the creator as an admin member.
    Redirects back to the dashboard.
    """
    from .models import Team

    if request.method != 'POST':
        return redirect('dashboard')

    name = (request.POST.get('name') or '').strip()
    if not name:
        # nothing provided, just go back
        return redirect('dashboard')

    team = Team(name=name, created_by=request.user)
    team.save()
    # add creator as admin
    team.add_member(request.user, is_admin=True)
    return redirect(f"{reverse('dashboard')}?joined={team.join_code}")


def signout(request):
    return render(request, 'account/signout.html')


@login_required
def set_wake_time(request, team_id):
    """POST endpoint to set current user's wake_time for a team.
    Expects JSON body: { "wake_time": "2025-11-13T07:30:00Z" } or { "wake_time": "now" }
    Returns JSON with awake_hours and over_limit.
    """
    from .models import Membership

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    membership = get_object_or_404(Membership, team_id=team_id, user=request.user)

    try:
        data = json.loads(request.body.decode()) if request.body else request.POST
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    wt = data.get('wake_time')
    if not wt:
        return JsonResponse({'error': 'wake_time required'}, status=400)

    if wt == 'now':
        dt = timezone.now()
    else:
        dt = parse_datetime(wt)
        if dt is None:
            return JsonResponse({'error': 'invalid datetime format'}, status=400)
        if timezone.is_naive(dt):
            # assume UTC when naive
            dt = timezone.make_aware(dt, timezone.utc)

    membership.set_wake_time(dt)
    return JsonResponse({
        'awake_hours': membership.awake_hours(),
        'over_limit': membership.is_over_awake_limit(),
    })

