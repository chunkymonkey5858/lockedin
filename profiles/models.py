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
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Longitude coordinate")
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

class PrivacySettings(models.Model):
    """Privacy settings for job seeker profiles"""

    LOCATION_VISIBILITY_CHOICES = [
        ('full', 'Full Address'),
        ('city', 'City Only'),
        ('state', 'State Only'),
        ('hidden', 'Hidden'),
    ]

    WORK_HISTORY_VISIBILITY_CHOICES = [
        ('all', 'Show All'),
        ('partial', 'Show Partial (Last 2 positions)'),
        ('hidden', 'Hidden'),
    ]

    PRIVACY_LEVEL_CHOICES = [
        ('public', 'Public - Everything visible'),
        ('limited', 'Limited - Basic info only'),
        ('private', 'Private - Minimal visibility'),
        ('custom', 'Custom - Manual selection'),
    ]

    # One-to-one relationship with JobSeekerProfile
    profile = models.OneToOneField(JobSeekerProfile, on_delete=models.CASCADE, related_name='privacy_settings')

    # Privacy Level Preset
    privacy_level = models.CharField(max_length=20, choices=PRIVACY_LEVEL_CHOICES, default='public')

    # Basic Information Privacy
    show_full_name = models.BooleanField(default=True, help_text="Show your full name")
    show_profile_photo = models.BooleanField(default=True, help_text="Show your profile photo")
    show_email = models.BooleanField(default=False, help_text="Show your email address")
    show_phone = models.BooleanField(default=False, help_text="Show your phone number")
    location_visibility = models.CharField(max_length=20, choices=LOCATION_VISIBILITY_CHOICES, default='city')

    # Professional Information Privacy
    show_current_employer = models.BooleanField(default=True, help_text="Show your current employer")
    work_history_visibility = models.CharField(max_length=20, choices=WORK_HISTORY_VISIBILITY_CHOICES, default='all')
    show_education = models.BooleanField(default=True, help_text="Show education history")
    show_skills = models.BooleanField(default=True, help_text="Show skills and certifications")
    show_resume = models.BooleanField(default=True, help_text="Allow resume downloads")

    # Additional Settings
    searchable_by_recruiters = models.BooleanField(default=True, help_text="Make profile searchable by recruiters")
    allow_recruiter_messages = models.BooleanField(default=True, help_text="Allow recruiters to message you")
    show_salary_expectations = models.BooleanField(default=False, help_text="Show salary expectations")

    # Blocked Companies
    blocked_companies = models.TextField(blank=True, help_text="Comma-separated list of company names to block")

    # Anonymous Mode
    anonymous_mode = models.BooleanField(default=False, help_text="Apply anonymously - hide identifying information")

    # Notifications
    notify_on_profile_view = models.BooleanField(default=False, help_text="Email notification when profile is viewed")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Privacy Settings'
        verbose_name_plural = 'Privacy Settings'

    def __str__(self):
        return f"Privacy Settings for {self.profile.user.username}"

    def apply_preset(self, preset):
        """Apply a privacy preset configuration"""
        if preset == 'public':
            self.show_full_name = True
            self.show_profile_photo = True
            self.show_email = True
            self.show_phone = True
            self.location_visibility = 'full'
            self.show_current_employer = True
            self.work_history_visibility = 'all'
            self.show_education = True
            self.show_skills = True
            self.show_resume = True
            self.searchable_by_recruiters = True
            self.allow_recruiter_messages = True
            self.show_salary_expectations = True
            self.anonymous_mode = False

        elif preset == 'limited':
            self.show_full_name = True
            self.show_profile_photo = True
            self.show_email = False
            self.show_phone = False
            self.location_visibility = 'city'
            self.show_current_employer = True
            self.work_history_visibility = 'partial'
            self.show_education = True
            self.show_skills = True
            self.show_resume = False
            self.searchable_by_recruiters = True
            self.allow_recruiter_messages = True
            self.show_salary_expectations = False
            self.anonymous_mode = False

        elif preset == 'private':
            self.show_full_name = False
            self.show_profile_photo = False
            self.show_email = False
            self.show_phone = False
            self.location_visibility = 'state'
            self.show_current_employer = False
            self.work_history_visibility = 'hidden'
            self.show_education = False
            self.show_skills = True
            self.show_resume = False
            self.searchable_by_recruiters = False
            self.allow_recruiter_messages = False
            self.show_salary_expectations = False
            self.anonymous_mode = True

        self.privacy_level = preset

    def get_blocked_companies_list(self):
        """Return list of blocked companies"""
        if self.blocked_companies:
            return [company.strip() for company in self.blocked_companies.split(',') if company.strip()]
        return []

    def is_company_blocked(self, company_name):
        """Check if a company is in the blocked list"""
        blocked_list = self.get_blocked_companies_list()
        return company_name.lower() in [company.lower() for company in blocked_list]

class Conversation(models.Model):
    """Represents a conversation between a recruiter and a job seeker"""
    recruiter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='recruiter_conversations')
    job_seeker = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='job_seeker_conversations')
    job_posting = models.ForeignKey('jobs.JobPosting', on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['recruiter', 'job_seeker', 'job_posting']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['recruiter', 'is_active']),
            models.Index(fields=['job_seeker', 'is_active']),
        ]
    
    def __str__(self):
        return f"Conversation: {self.recruiter.get_full_name()} ↔ {self.job_seeker.get_full_name()}"
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        if user == self.recruiter:
            return self.job_seeker
        return self.recruiter
    
    def get_latest_message(self):
        """Get the latest message in this conversation"""
        return self.messages.first()

class Message(models.Model):
    """Represents a message within a conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.get_full_name()} in {self.conversation}"
    
    def mark_as_read(self):
        """Mark this message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
