from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
from django.utils import timezone
import csv
from datetime import datetime, timedelta
from .models import CustomUser, JobSeekerProfile, Skill, Education, WorkExperience, Link, Notification, AdminActionLog, UserActivity

class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff']
    list_filter = ['user_type', 'is_staff', 'is_superuser', 'is_active']
    actions = ['export_selected_users_csv', 'export_all_users_csv', 'export_usage_metrics_action']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type',)}),
    )
    
    def export_selected_users_csv(self, request, queryset):
        """Export selected users to CSV"""
        return self._export_users_csv(queryset)
    export_selected_users_csv.short_description = "Export selected users to CSV"
    
    def export_all_users_csv(self, request, queryset):
        """Export all users to CSV"""
        all_users = CustomUser.objects.all()
        return self._export_users_csv(all_users)
    export_all_users_csv.short_description = "Export all users to CSV"
    
    def _export_users_csv(self, queryset):
        """Helper method to export users to CSV"""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="users_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        response.write('\ufeff')  # BOM for Excel
        
        writer = csv.writer(response)
        writer.writerow([
            'Username', 'Email', 'First Name', 'Last Name', 'User Type', 
            'Status', 'Is Superuser', 'Is Staff', 'Date Joined', 'Last Login',
            'Has Job Seeker Profile', 'Has Recruiter Profile'
        ])
        
        for user in queryset.select_related('job_seeker_profile').order_by('-date_joined'):
            try:
                has_job_seeker = user.job_seeker_profile is not None
            except JobSeekerProfile.DoesNotExist:
                has_job_seeker = False
            
            try:
                from recruiters.models import RecruiterProfile
                has_recruiter = RecruiterProfile.objects.filter(user=user).exists()
            except:
                has_recruiter = False
            
            writer.writerow([
                user.username,
                user.email,
                user.first_name or '',
                user.last_name or '',
                user.get_user_type_display(),
                user.get_status_display(),
                'Yes' if user.is_superuser else 'No',
                'Yes' if user.is_staff else 'No',
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else '',
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
                'Yes' if has_job_seeker else 'No',
                'Yes' if has_recruiter else 'No',
            ])
        
        return response

class SkillInline(admin.TabularInline):
    model = Skill
    extra = 3

class EducationInline(admin.TabularInline):
    model = Education
    extra = 1

class WorkExperienceInline(admin.TabularInline):
    model = WorkExperience
    extra = 1

class LinkInline(admin.TabularInline):
    model = Link
    extra = 2

@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'headline', 'location', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'headline', 'location']
    
    inlines = [SkillInline, EducationInline, WorkExperienceInline, LinkInline]

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Skill)
admin.site.register(Education)
admin.site.register(WorkExperience)
admin.site.register(Link)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
    readonly_fields = ('created_at', 'read_at')

@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    list_display = ('admin_user', 'target_user', 'action_type', 'created_at')
    list_filter = ('action_type', 'created_at')
    search_fields = ('admin_user__username', 'target_user__username', 'description')
    readonly_fields = ('created_at',)
    actions = ['export_selected_logs_csv', 'export_all_logs_csv']
    date_hierarchy = 'created_at'
    
    def export_selected_logs_csv(self, request, queryset):
        """Export selected admin action logs to CSV"""
        return self._export_logs_csv(queryset)
    export_selected_logs_csv.short_description = "Export selected logs to CSV"
    
    def export_all_logs_csv(self, request, queryset):
        """Export all admin action logs to CSV"""
        all_logs = AdminActionLog.objects.all()
        return self._export_logs_csv(all_logs)
    export_all_logs_csv.short_description = "Export all logs to CSV"
    
    def _export_logs_csv(self, queryset):
        """Helper method to export admin action logs to CSV"""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="admin_actions_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Admin User', 'Admin Email', 'Target User', 'Target Email',
            'Action Type', 'Description', 'Previous Value', 'New Value',
            'IP Address', 'User Agent', 'Created At'
        ])
        
        for log in queryset.select_related('admin_user', 'target_user').order_by('-created_at'):
            writer.writerow([
                log.id,
                log.admin_user.username if log.admin_user else '',
                log.admin_user.email if log.admin_user else '',
                log.target_user.username if log.target_user else '',
                log.target_user.email if log.target_user else '',
                log.get_action_type_display(),
                log.description,
                log.previous_value,
                log.new_value,
                str(log.ip_address) if log.ip_address else '',
                log.user_agent[:200] if log.user_agent else '',
                log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else '',
            ])
        
        return response

# Add usage metrics export as an admin action available on any model
def export_usage_metrics_action(modeladmin, request, queryset):
    """Export usage metrics to CSV - available as admin action"""
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="usage_metrics_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    response.write('\ufeff')
    
    writer = csv.writer(response)
    writer.writerow(['Metric', 'Value', 'Period', 'Date'])
    
    now = timezone.now()
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # User metrics
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(status='active').count()
    job_seekers = CustomUser.objects.filter(user_type='job_seeker').count()
    recruiters = CustomUser.objects.filter(user_type='recruiter').count()
    
    # Job metrics
    from jobs.models import JobPosting, JobApplication
    total_jobs = JobPosting.objects.count()
    active_jobs = JobPosting.objects.filter(is_active=True).count()
    published_jobs = JobPosting.objects.filter(status='published').count()
    
    # Application metrics
    total_applications = JobApplication.objects.count()
    applications_this_month = JobApplication.objects.filter(
        applied_at__gte=first_day_of_month
    ).count()
    
    # Recent registrations
    users_today = CustomUser.objects.filter(date_joined__date=now.date()).count()
    users_this_week = CustomUser.objects.filter(
        date_joined__gte=now - timedelta(days=7)
    ).count()
    users_this_month = CustomUser.objects.filter(
        date_joined__gte=first_day_of_month
    ).count()
    
    # Write metrics
    metrics = [
        ('Total Users', total_users, 'All Time', now.strftime('%Y-%m-%d')),
        ('Active Users', active_users, 'All Time', now.strftime('%Y-%m-%d')),
        ('Job Seekers', job_seekers, 'All Time', now.strftime('%Y-%m-%d')),
        ('Recruiters', recruiters, 'All Time', now.strftime('%Y-%m-%d')),
        ('Total Job Postings', total_jobs, 'All Time', now.strftime('%Y-%m-%d')),
        ('Active Job Postings', active_jobs, 'All Time', now.strftime('%Y-%m-%d')),
        ('Published Job Postings', published_jobs, 'All Time', now.strftime('%Y-%m-%d')),
        ('Total Applications', total_applications, 'All Time', now.strftime('%Y-%m-%d')),
        ('Applications This Month', applications_this_month, 'This Month', now.strftime('%Y-%m-%d')),
        ('New Users Today', users_today, 'Today', now.strftime('%Y-%m-%d')),
        ('New Users This Week', users_this_week, 'This Week', now.strftime('%Y-%m-%d')),
        ('New Users This Month', users_this_month, 'This Month', now.strftime('%Y-%m-%d')),
    ]
    
    for metric, value, period, date in metrics:
        writer.writerow([metric, value, period, date])
    
    # Time series data - registrations by day (last 30 days)
    writer.writerow([])  # Empty row separator
    writer.writerow(['Date', 'New Registrations', 'New Job Postings', 'New Applications'])
    
    for i in range(30):
        date = now.date() - timedelta(days=i)
        date_start = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        date_end = date_start + timedelta(days=1)
        
        registrations = CustomUser.objects.filter(
            date_joined__gte=date_start,
            date_joined__lt=date_end
        ).count()
        
        job_postings = JobPosting.objects.filter(
            posted_at__gte=date_start,
            posted_at__lt=date_end
        ).count()
        
        applications = JobApplication.objects.filter(
            applied_at__gte=date_start,
            applied_at__lt=date_end
        ).count()
        
        writer.writerow([
            date.strftime('%Y-%m-%d'),
            registrations,
            job_postings,
            applications
        ])
    
    return response

export_usage_metrics_action.short_description = "Export Usage Metrics to CSV"

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'timestamp', 'ip_address')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__username', 'user__email', 'details')
    readonly_fields = ('timestamp',)
    actions = ['export_selected_activities_csv', 'export_all_activities_csv']
    date_hierarchy = 'timestamp'
    
    def export_selected_activities_csv(self, request, queryset):
        """Export selected user activities to CSV"""
        return self._export_activities_csv(queryset)
    export_selected_activities_csv.short_description = "Export selected activities to CSV"
    
    def export_all_activities_csv(self, request, queryset):
        """Export all user activities to CSV"""
        all_activities = UserActivity.objects.all()
        return self._export_activities_csv(all_activities)
    export_all_activities_csv.short_description = "Export all activities to CSV"
    
    def _export_activities_csv(self, queryset):
        """Helper method to export user activities to CSV"""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="user_activities_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'User', 'Email', 'Activity Type', 'Timestamp', 'IP Address', 'Details'
        ])
        
        for activity in queryset.select_related('user').order_by('-timestamp'):
            writer.writerow([
                activity.id,
                activity.user.username if activity.user else '',
                activity.user.email if activity.user else '',
                activity.get_activity_type_display(),
                activity.timestamp.strftime('%Y-%m-%d %H:%M:%S') if activity.timestamp else '',
                str(activity.ip_address) if activity.ip_address else '',
                activity.details[:500] if activity.details else '',  # Limit details length
            ])
        
        return response
