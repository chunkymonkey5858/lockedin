from django.contrib import admin
from .models import RecruiterProfile, SavedSearch, CandidateNote, SearchMatch, SearchNotification

@admin.register(RecruiterProfile)
class RecruiterProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'title', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'company']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ['name', 'recruiter', 'location', 'experience_level', 'is_active', 'notify_on_new_matches', 'notification_frequency', 'created_at']
    list_filter = ['is_active', 'notify_on_new_matches', 'notification_frequency', 'experience_level', 'employment_type', 'created_at']
    search_fields = ['name', 'description', 'recruiter__user__username']
    filter_horizontal = ['skills']
    readonly_fields = ['created_at', 'updated_at', 'last_notified_at', 'last_search_at']

@admin.register(CandidateNote)
class CandidateNoteAdmin(admin.ModelAdmin):
    list_display = ['recruiter', 'candidate', 'is_private', 'created_at']
    list_filter = ['is_private', 'created_at']
    search_fields = ['recruiter__user__username', 'candidate__user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SearchMatch)
class SearchMatchAdmin(admin.ModelAdmin):
    list_display = ['saved_search', 'candidate', 'matched_at', 'is_new_match', 'notified']
    list_filter = ['is_new_match', 'notified', 'matched_at', 'saved_search__recruiter']
    search_fields = ['saved_search__name', 'candidate__user__username', 'candidate__user__first_name', 'candidate__user__last_name']
    readonly_fields = ['matched_at']
    date_hierarchy = 'matched_at'


@admin.register(SearchNotification)
class SearchNotificationAdmin(admin.ModelAdmin):
    list_display = ['saved_search', 'notification_type', 'sent_at', 'matches_count', 'is_read', 'email_sent']
    list_filter = ['notification_type', 'is_read', 'email_sent', 'sent_at', 'saved_search__recruiter']
    search_fields = ['saved_search__name', 'saved_search__recruiter__user__username']
    readonly_fields = ['sent_at']
    date_hierarchy = 'sent_at'
