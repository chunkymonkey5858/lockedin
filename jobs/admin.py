from django.contrib import admin
from .models import JobCategory, JobPosting, JobApplication, JobSkill

@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name', 'description']

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'posted_by', 'location', 'is_active', 'posted_at']
    list_filter = ['is_active', 'employment_type', 'experience_level', 'work_location', 'category', 'posted_at']
    search_fields = ['title', 'company', 'location', 'description', 'posted_by__username', 'posted_by__first_name', 'posted_by__last_name']
    readonly_fields = ['posted_at', 'updated_at', 'view_count', 'application_count']
    actions = ['deactivate_jobs', 'activate_jobs', 'delete_selected']
    
    def deactivate_jobs(self, request, queryset):
        """Deactivate selected job postings"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} job postings have been deactivated.')
    deactivate_jobs.short_description = "Deactivate selected jobs"
    
    def activate_jobs(self, request, queryset):
        """Activate selected job postings"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} job postings have been activated.')
    activate_jobs.short_description = "Activate selected jobs"

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
