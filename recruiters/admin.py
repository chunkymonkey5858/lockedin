from django.contrib import admin
from .models import RecruiterProfile, SavedSearch, CandidateNote

@admin.register(RecruiterProfile)
class RecruiterProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'title', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'company']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ['name', 'recruiter', 'location', 'experience_level', 'is_active', 'created_at']
    list_filter = ['is_active', 'experience_level', 'employment_type', 'created_at']
    search_fields = ['name', 'description', 'recruiter__user__username']
    filter_horizontal = ['skills']

@admin.register(CandidateNote)
class CandidateNoteAdmin(admin.ModelAdmin):
    list_display = ['recruiter', 'candidate', 'is_private', 'created_at']
    list_filter = ['is_private', 'created_at']
    search_fields = ['recruiter__user__username', 'candidate__user__username']
    readonly_fields = ['created_at', 'updated_at']
