import uuid
import string
import secrets
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = settings.AUTH_USER_MODEL

# function to generate a unique join code - we call it in join_code field default
def make_join_code(length=6):
    # Uppercase letters + digits, avoid ambiguous chars; use secrets for better randomness
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# Awake limits
MAX_AWAKE_HOURS = 17
MAX_AWAKE_SECONDS = MAX_AWAKE_HOURS * 3600


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    members = models.ManyToManyField(User, through='Membership', related_name='teams')
    join_code = models.CharField(max_length=12, unique=True, db_index=True, default=make_join_code)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='created_teams')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    timezone = models.CharField(max_length=50, blank=True, null=True)
    wake_time = models.TimeField(blank=True, null=True)
    duration = models.TimeField(blank=True, null=True)

    def get_awake_duration(self):
        """Calculate how long this member has been awake."""
        if not self.timezone or not self.wake_time:
            return None
    
        from datetime import timedelta
        from django.utils import timezone as tz
        from zoneinfo import ZoneInfo
        
        # Parse timezone offset from string like "GMT+5" or "GMT-3"
        timezone_offset = int(self.timezone.replace('GMT', '').replace('+', ''))
    
        # Get hour and minute from TimeField
        awake_hour = self.wake_time.hour
        awake_minute = self.wake_time.minute
        wake_local = awake_hour * 60 + awake_minute

        # Convert wake time (local) to UTC minutes
        wake_utc_minutes = wake_local - (timezone_offset * 60)

        # Current UTC time in minutes
        now_utc = tz.now().astimezone(ZoneInfo('UTC'))
        now_utc_minutes = now_utc.hour * 60 + now_utc.minute

        # Time awake, handle day rollover
        minutes_awake = (now_utc_minutes - wake_utc_minutes + 1440) % 1440

        # Return hours as a formatted string
        hours = minutes_awake / 60
        return f"{hours:.1f}h"