from django.contrib import admin

# Register your models here.
from .models import Team, Membership, Profile

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'created_at')
    search_fields = ('name', 'join_code', 'created_by__username')
    readonly_fields = ('join_code',)

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('team', 'user', 'role', 'is_admin', 'joined_at', 'awake_display', 'is_over_awake_limit')
    list_filter = ('role', 'is_admin')
    search_fields = ('team__name', 'user__username', 'user__email')

    def awake_display(self, obj):
        if not obj.wake_time:
            return '—'
        return f"{obj.awake_hours()}h (woke at {obj.wake_time.strftime('%Y-%m-%d %H:%M %Z')})"
    awake_display.short_description = 'Awake'

    def is_over_awake_limit(self, obj):
        return obj.is_over_awake_limit()
    is_over_awake_limit.boolean = True
    is_over_awake_limit.short_description = 'Over limit'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'timezone', 'wake_time')
    search_fields = ('user__username', 'user__email', 'timezone')