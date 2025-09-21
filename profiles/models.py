from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import URLValidator
from django.utils import timezone

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('job_seeker', 'Job Seeker'),
        ('recruiter', 'Recruiter'),
        ('admin', 'Administrator'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('flagged', 'Flagged'),
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='job_seeker')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def is_active_user(self):
        """Check if user is active (not suspended)"""
        return self.status == 'active'
    
    def is_flagged(self):
        """Check if user is flagged for suspicious activity"""
        return self.status == 'flagged'

class JobSeekerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='job_seeker_profile')
    headline = models.CharField(max_length=200, help_text="Professional headline or title")
    bio = models.TextField(max_length=1000, blank=True, help_text="Brief professional summary")
    location = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    is_public = models.BooleanField(default=True, help_text="Make profile visible to recruiters")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.headline}"

class Skill(models.Model):
    SKILL_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=20, choices=SKILL_LEVELS, default='intermediate')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['profile', 'name']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.level})"

class Education(models.Model):
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='education')
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True, help_text="Leave blank if currently enrolled")
    gpa = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    description = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.degree} at {self.institution}"
    
    @property
    def is_current(self):
        return self.end_date is None or self.end_date > timezone.now().date()

class WorkExperience(models.Model):
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='work_experience')
    company = models.CharField(max_length=200)
    position = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True, help_text="Leave blank if currently employed")
    description = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.position} at {self.company}"
    
    @property
    def is_current(self):
        return self.end_date is None or self.end_date > timezone.now().date()

class Link(models.Model):
    LINK_TYPES = [
        ('portfolio', 'Portfolio'),
        ('github', 'GitHub'),
        ('linkedin', 'LinkedIn'),
        ('website', 'Personal Website'),
        ('blog', 'Blog'),
        ('other', 'Other'),
    ]
    
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='links')
    title = models.CharField(max_length=100)
    url = models.URLField()
    link_type = models.CharField(max_length=20, choices=LINK_TYPES, default='other')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['link_type', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.link_type})"

class AdminActionLog(models.Model):
    ACTION_TYPES = [
        ('suspend', 'Suspend User'),
        ('reactivate', 'Reactivate User'),
        ('delete', 'Delete User'),
        ('change_role', 'Change User Role'),
        ('flag', 'Flag User'),
        ('unflag', 'Unflag User'),
    ]
    
    admin_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='admin_actions')
    target_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='admin_action_targets')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField(help_text="Description of the action taken")
    previous_value = models.CharField(max_length=200, blank=True, help_text="Previous value before change")
    new_value = models.CharField(max_length=200, blank=True, help_text="New value after change")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Admin Action Log'
        verbose_name_plural = 'Admin Action Logs'
    
    def __str__(self):
        return f"{self.admin_user.username} {self.get_action_type_display()} {self.target_user.username} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"
