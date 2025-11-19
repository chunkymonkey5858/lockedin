from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
import csv
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
    actions = ['deactivate_jobs', 'activate_jobs', 'export_selected_jobs_csv', 'export_all_jobs_csv']
    
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
    
    def export_selected_jobs_csv(self, request, queryset):
        """Export selected job postings to CSV"""
        return self._export_jobs_csv(queryset)
    export_selected_jobs_csv.short_description = "Export selected jobs to CSV"
    
    def export_all_jobs_csv(self, request, queryset):
        """Export all job postings to CSV"""
        from .models import JobPosting
        all_jobs = JobPosting.objects.all()
        return self._export_jobs_csv(all_jobs)
    export_all_jobs_csv.short_description = "Export all jobs to CSV"
    
    def _export_jobs_csv(self, queryset):
        """Helper method to export job postings to CSV"""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="job_postings_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Title', 'Company', 'Location', 'Category', 'Employment Type',
            'Experience Level', 'Work Location', 'Status', 'Is Active',
            'Salary Min', 'Salary Max', 'Salary Currency', 'Salary Period',
            'Visa Sponsorship', 'Application Count', 'View Count',
            'Posted By (Email)', 'Posted By (Username)', 'Posted At', 'Updated At'
        ])
        
        for job in queryset.select_related('posted_by', 'category').prefetch_related('required_skills').order_by('-posted_at'):
            writer.writerow([
                job.id,
                job.title or '',
                job.company or '',
                job.location or '',
                job.category.name if job.category else '',
                job.get_employment_type_display(),
                job.get_experience_level_display(),
                job.get_work_location_display(),
                job.get_status_display(),
                'Yes' if job.is_active else 'No',
                str(job.salary_min) if job.salary_min else '',
                str(job.salary_max) if job.salary_max else '',
                job.salary_currency,
                job.salary_period,
                'Yes' if job.visa_sponsorship else 'No',
                job.application_count,
                job.view_count,
                job.posted_by.email if job.posted_by else '',
                job.posted_by.username if job.posted_by else '',
                job.posted_at.strftime('%Y-%m-%d %H:%M:%S') if job.posted_at else '',
                job.updated_at.strftime('%Y-%m-%d %H:%M:%S') if job.updated_at else '',
            ])
        
        return response

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'job', 'status', 'applied_at']
    list_filter = ['status', 'applied_at']
    search_fields = ['applicant__username', 'job__title', 'job__company']
    readonly_fields = ['applied_at', 'updated_at']
    actions = ['export_selected_applications_csv', 'export_all_applications_csv']
    
    def export_selected_applications_csv(self, request, queryset):
        """Export selected applications to CSV"""
        return self._export_applications_csv(queryset)
    export_selected_applications_csv.short_description = "Export selected applications to CSV"
    
    def export_all_applications_csv(self, request, queryset):
        """Export all applications to CSV"""
        from .models import JobApplication
        all_applications = JobApplication.objects.all()
        return self._export_applications_csv(all_applications)
    export_all_applications_csv.short_description = "Export all applications to CSV"
    
    def _export_applications_csv(self, queryset):
        """Helper method to export applications to CSV"""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="job_applications_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Job Title', 'Job Company', 'Applicant Email', 'Applicant Username',
            'Applicant Name', 'Status', 'Outcome', 'Applied At', 'Interview Date',
            'Has Resume', 'Has Cover Letter'
        ])
        
        for app in queryset.select_related('job', 'applicant', 'job__posted_by').order_by('-applied_at'):
            applicant_name = app.applicant.get_full_name() or app.applicant.username
            
            writer.writerow([
                app.id,
                app.job.title if app.job else '',
                app.job.company if app.job else '',
                app.applicant.email if app.applicant else '',
                app.applicant.username if app.applicant else '',
                applicant_name,
                app.get_status_display(),
                app.get_outcome_display(),
                app.applied_at.strftime('%Y-%m-%d %H:%M:%S') if app.applied_at else '',
                app.interview_date.strftime('%Y-%m-%d %H:%M:%S') if app.interview_date else '',
                'Yes' if app.resume else 'No',
                'Yes' if app.cover_letter else 'No',
            ])
        
        return response

@admin.register(JobSkill)
class JobSkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'job', 'is_required', 'years_experience']
    list_filter = ['is_required', 'job__category']
    search_fields = ['name', 'job__title']
