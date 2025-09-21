from django.contrib import admin
from .models import JobCategory, JobPosting, JobApplication, JobSkill

@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name', 'description']

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'location', 'employment_type', 'experience_level', 'is_active', 'posted_at']
    list_filter = ['is_active', 'employment_type', 'experience_level', 'work_location', 'category', 'posted_at']
    search_fields = ['title', 'company', 'location', 'description']
    readonly_fields = ['posted_at', 'updated_at', 'view_count', 'application_count']

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'job', 'status', 'applied_at']
    list_filter = ['status', 'applied_at']
    search_fields = ['applicant__username', 'job__title', 'job__company']
    readonly_fields = ['applied_at', 'updated_at']

@admin.register(JobSkill)
class JobSkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'job', 'is_required', 'years_experience']
    list_filter = ['is_required', 'job__category']
    search_fields = ['name', 'job__title']
