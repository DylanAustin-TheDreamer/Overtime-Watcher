from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.http import JsonResponse
from django.contrib import messages
import json
from zoneinfo import ZoneInfo
from .utils.timezones import timezone_choices
from django.apps import apps

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
    # timezone choices for profile dropdown
    tz_choices = timezone_choices()

    # Compute per-team "my awake" hours using membership wake_time if present,
    # otherwise fall back to a user-level wake_time stored in session or profile.
    now = timezone.now()
    # try to get a user-level wake_time from session or profile
    user_wt = None
    if request.session.get('user_wake_time'):
        user_wt = parse_datetime(request.session.get('user_wake_time'))
        if user_wt and timezone.is_naive(user_wt):
            user_wt = timezone.make_aware(user_wt, timezone.utc)
    else:
        try:
            profile = getattr(request.user, 'profile', None)
            if profile is not None and hasattr(profile, 'wake_time') and profile.wake_time:
                user_wt = profile.wake_time
        except Exception:
            user_wt = None

    from .models import MAX_AWAKE_SECONDS
    for t in teams:
        # find membership for current user
        m = None
        try:
            m = t.memberships.filter(user=request.user).first()
        except Exception:
            m = None

        if m and getattr(m, 'wake_time', None):
            val = m.awake_hours()
            dt_for_display = m.wake_time
        elif user_wt:
            delta = (now - user_wt).total_seconds()
            secs = max(0, int(delta))
            secs = min(secs, MAX_AWAKE_SECONDS)
            val = round(secs / 3600.0, 2)
            # user_wt is an aware datetime
            dt_for_display = user_wt
        else:
            val = 0.0
            dt_for_display = None
        # attach to team object for easy template access
        try:
            t.my_awake = val
            t.user_wake_time_iso = dt_for_display.isoformat() if dt_for_display is not None else ''
        except Exception:
            pass

    return render(request, 'dashboard.html', { 'teams': teams, 'timezone_choices': tz_choices })

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
    # if this is a newly-created membership, try to seed its wake_time from
    # persisted Profile or from the session-stored user_wake_time so the
    # dashboard shows a value immediately.
    if created:
        try:
            Profile = apps.get_model('overtime', 'Profile')
            profile = getattr(request.user, 'profile', None)
            if profile is None:
                # possibly an older user without Profile; try to create one
                try:
                    profile = Profile.objects.create(user=request.user)
                except Exception:
                    profile = None

            copied = False
            if profile is not None and getattr(profile, 'wake_time', None) and not getattr(membership, 'wake_time', None):
                membership.wake_time = profile.wake_time
                membership.save(update_fields=['wake_time'])
                copied = True

            # fallback: if we had a session-level wake_time string, use that
            if not copied and request.session.get('user_wake_time'):
                try:
                    wt = parse_datetime(request.session.get('user_wake_time'))
                    if wt is not None:
                        if timezone.is_naive(wt):
                            wt = timezone.make_aware(wt, timezone.utc)
                        membership.wake_time = wt
                        membership.save(update_fields=['wake_time'])
                        copied = True
                except Exception:
                    pass

            # ensure the membership exists in DB at least once
            if not copied:
                membership.save()
        except Exception:
            try:
                membership.save()
            except Exception:
                pass
    else:
        # existing membership; ensure it's saved
        try:
            membership.save()
        except Exception:
            pass
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

@login_required
def profile_update(request):
    """Handle profile update form POST.
    Expects `timezone` in POST. Updates the user's timezone preference.
    Redirects back to the dashboard.
    """
    if request.method != 'POST':
        return redirect('dashboard')

    tz = (request.POST.get('timezone') or '').strip()
    if not tz:
        messages.error(request, 'No timezone selected.')
        return redirect('dashboard')

    # Save timezone to session so it's available immediately
    request.session['user_timezone'] = tz

    # Also accept an optional wake_time field from the profile form
    wake = (request.POST.get('wake_time') or '').strip()
    if wake:
        # try to parse and make aware using selected timezone
        dt = parse_datetime(wake)
        if dt is None and len(wake) == 16:
            # append seconds and try again
            try:
                dt = parse_datetime(wake + ':00')
            except Exception:
                dt = None
        if dt is not None:
            if timezone.is_naive(dt):
                try:
                    dt = timezone.make_aware(dt, ZoneInfo(tz))
                except Exception:
                    dt = timezone.make_aware(dt, timezone.utc)
            # store the ISO string in session
            request.session['user_wake_time'] = dt.isoformat()

    # If user has a profile model with a timezone/wake_time field, try to save there too
    try:
        # Ensure a Profile exists for this user (for older users created before
        # the Profile model or signal were added).
        Profile = apps.get_model('overtime', 'Profile')
        profile = getattr(request.user, 'profile', None)
        if profile is None:
            # create a profile for this user
            try:
                profile = Profile.objects.create(user=request.user)
            except Exception:
                profile = None

        if profile is not None:
            if hasattr(profile, 'timezone'):
                profile.timezone = tz
            if wake and hasattr(profile, 'wake_time') and dt is not None:
                profile.wake_time = dt
            profile.save()
            # If the user updated their account wake_time, propagate it to
            # all of their memberships so each team shows the updated value.
            if wake and dt is not None:
                try:
                    from .models import Membership
                    memberships = Membership.objects.filter(user=request.user)
                    for m in memberships:
                        try:
                            m.set_wake_time(dt)
                        except Exception:
                            # ignore individual membership failures
                            pass
                except Exception:
                    # ignore failures to propagate
                    pass
    except Exception:
        # ignore failures to persist profile (we still saved timezone to session)
        pass

    messages.success(request, 'Profile saved.')
    return redirect('dashboard')


@login_required
def set_wake_time_form(request, team_id):
    """Handle form POST of wake_time (from datetime-local input).
    Expects `wake_time` in POST (ISO-like string from datetime-local) or 'now'.
    Redirects to dashboard.
    """
    from .models import Membership

    if request.method != 'POST':
        return redirect('dashboard')

    membership = get_object_or_404(Membership, team_id=team_id, user=request.user)

    wt = (request.POST.get('wake_time') or '').strip()
    if not wt:
        messages.error(request, 'No wake time provided.')
        return redirect('dashboard')

    if wt == 'now':
        dt = timezone.now()
    else:
        # parse common input formats
        dt = parse_datetime(wt)
        if dt is None:
            # try to accept datetime-local (no timezone) format like 'YYYY-MM-DDTHH:MM'
            try:
                # append seconds if missing
                if len(wt) == 16:
                    wt = wt + ':00'
                dt = parse_datetime(wt)
            except Exception:
                dt = None

        if dt is None:
            messages.error(request, 'Invalid datetime format.')
            return redirect('dashboard')

        if timezone.is_naive(dt):
            # prefer user's saved timezone, else assume UTC
            user_tz = request.session.get('user_timezone')
            try:
                if not user_tz:
                    profile = getattr(request.user, 'profile', None)
                    user_tz = getattr(profile, 'timezone', None) if profile is not None else None
                if user_tz:
                    dt = timezone.make_aware(dt, ZoneInfo(user_tz))
                else:
                    dt = timezone.make_aware(dt, timezone.utc)
            except Exception:
                dt = timezone.make_aware(dt, timezone.utc)

    membership.set_wake_time(dt)
    messages.success(request, 'Wake time set.')
    return redirect('dashboard')

@login_required
def force_model_save_wake_time(request):
    """Force user Membership models to re-save their wake_time field"""

    if request.method != 'POST':
        return redirect('dashboard')
    
    from .models import Membership
    # Only operate on the current user's memberships (don't touch other users)
    memberships = Membership.objects.filter(user=request.user)

    # Prefer a persisted account-level wake_time (Profile), then session value.
    wt = None
    try:
        profile = getattr(request.user, 'profile', None)
        if profile is not None and getattr(profile, 'wake_time', None):
            wt = profile.wake_time
    except Exception:
        wt = None

    if not wt and request.session.get('user_wake_time'):
        try:
            wt = parse_datetime(request.session.get('user_wake_time'))
            if wt and timezone.is_naive(wt):
                wt = timezone.make_aware(wt, timezone.utc)
        except Exception:
            wt = None

    updated = 0
    if wt:
        # copy the account/session wake_time into each membership
        for m in memberships:
            try:
                m.set_wake_time(wt)
                updated += 1
            except Exception:
                pass
    else:
        # No account wake_time: re-save each membership's existing wake_time
        # to normalize/force any side-effects.
        for m in memberships:
            if getattr(m, 'wake_time', None):
                try:
                    m.set_wake_time(m.wake_time)
                    updated += 1
                except Exception:
                    pass

    messages.success(request, f'Updated wake_time on {updated} membership(s).')
    return redirect('dashboard')

