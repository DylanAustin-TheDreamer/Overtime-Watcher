from django.contrib import admin

# Register your models here.
from .models import Team

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'created_at')
    search_fields = ('name', 'join_code', 'created_by__username')
    readonly_fields = ('join_code',)