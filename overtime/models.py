import uuid
import string
import secrets
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    members = models.ManyToManyField(User, through='Membership', related_name='teams')
    join_code = models.CharField(max_length=12, unique=True, db_index=True, default=make_join_code)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_teams')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    joined_at = models.DateTimeField(auto_now_add=True)