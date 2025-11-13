import uuid
import random
import string
import secrets
from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL

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
    join_code = models.CharField(max_length=12, unique=True, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_teams')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('-created_at',)

    def save(self, *args, **kwargs):
        # ensure unique join_code
        if not self.join_code:
            for _ in range(10):
                code = make_join_code(6)
                if not Team.objects.filter(join_code=code).exists():
                    self.join_code = code
                    break
            else:
                # fallback to uuid-based code
                self.join_code = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} ({self.join_code})'

    def add_member(self, user, is_admin=False):
        membership, created = Membership.objects.get_or_create(team=self, user=user, defaults={'is_admin': is_admin})
        return membership, created

    @classmethod
    def join_by_code(cls, code, user, is_admin=False):
        try:
            team = cls.objects.get(join_code=code.upper())
        except cls.DoesNotExist:
            return None, False
        membership, created = Membership.objects.get_or_create(team=team, user=user, defaults={'is_admin': is_admin})
        return team, created


class Membership(models.Model):
    ROLE_CHOICES = (
        ('member', 'Member'),
        ('manager', 'Manager'),
        ('owner', 'Owner'),
    )

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    # time tracking fields (original clock-in/out style)
    last_clock_in = models.DateTimeField(null=True, blank=True)
    currently_clocked_in = models.BooleanField(default=False)
    total_seconds = models.BigIntegerField(default=0)      # cumulative seconds worked for this team
    overtime_seconds = models.BigIntegerField(default=0)   # cumulative overtime seconds for this team

    # Wake-time based tracking (user sets when they woke up; we compute awake duration)
    wake_time = models.DateTimeField(null=True, blank=True, help_text="Timestamp when user woke up (UTC)")

    class Meta:
        unique_together = ('team', 'user')
        ordering = ('-joined_at',)

    def __str__(self):
        return f'{self.user} @ {self.team}'

    def clock_in(self):
        if not self.currently_clocked_in:
            self.last_clock_in = timezone.now()
            self.currently_clocked_in = True
            self.save(update_fields=['last_clock_in', 'currently_clocked_in'])

    def clock_out(self):
        if self.currently_clocked_in and self.last_clock_in:
            now = timezone.now()
            delta = (now - self.last_clock_in).total_seconds()
            self.total_seconds = (self.total_seconds or 0) + int(delta)
            # optionally compute overtime_seconds here
            self.last_clock_in = None
            self.currently_clocked_in = False
            self.save(update_fields=['total_seconds', 'last_clock_in', 'currently_clocked_in'])

    # --- wake-time helpers ---
    def set_wake_time(self, dt):
        """Set wake_time to a timezone-aware datetime (dt should be timezone-aware)."""
        self.wake_time = dt
        self.save(update_fields=['wake_time'])

    def clear_wake_time(self):
        self.wake_time = None
        self.save(update_fields=['wake_time'])

    def awake_seconds(self, at_time=None):
        """Return seconds awake, capped at MAX_AWAKE_SECONDS."""
        if not self.wake_time:
            return 0
        now = at_time or timezone.now()
        delta = now - self.wake_time
        secs = max(0, int(delta.total_seconds()))
        return min(secs, MAX_AWAKE_SECONDS)

    def awake_hours(self, at_time=None, rounded=2):
        secs = self.awake_seconds(at_time=at_time)
        hours = secs / 3600.0
        return round(hours, rounded)

    def is_over_awake_limit(self, at_time=None):
        return self.awake_seconds(at_time=at_time) >= MAX_AWAKE_SECONDS