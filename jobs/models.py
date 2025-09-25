from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()

class JobCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Job Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class JobPosting(models.Model):
    EMPLOYMENT_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('temporary', 'Temporary'),
    ]
    
    EXPERIENCE_LEVELS = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive'),
    ]
    
    WORK_LOCATIONS = [
        ('remote', 'Remote'),
        ('on_site', 'On Site'),
        ('hybrid', 'Hybrid'),
    ]
    
    # Basic job information
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    work_location = models.CharField(max_length=20, choices=WORK_LOCATIONS, default='on_site')
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='full_time')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, default='mid')
    
    # Job details
    description = models.TextField()
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    
    # Compensation
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='USD')
    salary_period = models.CharField(max_length=20, default='yearly', choices=[
        ('hourly', 'Per Hour'),
        ('monthly', 'Per Month'),
        ('yearly', 'Per Year'),
    ])
    
    # Relationships
    category = models.ForeignKey(JobCategory, on_delete=models.CASCADE, related_name='jobs')
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    
    # Status and dates
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    application_deadline = models.DateField(null=True, blank=True)
    posted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Application tracking
    application_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    
    # Additional job features
    visa_sponsorship = models.BooleanField(default=False, help_text="Does this job offer visa sponsorship?")
    
    class Meta:
        ordering = ['-posted_at']
        indexes = [
            models.Index(fields=['is_active', 'posted_at']),
            models.Index(fields=['category', 'location']),
            models.Index(fields=['employment_type', 'experience_level']),
        ]
    
    def __str__(self):
        return f"{self.title} at {self.company}"
    
    @property
    def is_expired(self):
        if self.application_deadline:
            return self.application_deadline < timezone.now().date()
        return False
    
    @property
    def salary_range(self):
        if self.salary_min and self.salary_max:
            return f"${self.salary_min:,.0f} - ${self.salary_max:,.0f} {self.salary_currency}/{self.salary_period}"
        elif self.salary_min:
            return f"${self.salary_min:,.0f}+ {self.salary_currency}/{self.salary_period}"
        elif self.salary_max:
            return f"Up to ${self.salary_max:,.0f} {self.salary_currency}/{self.salary_period}"
        return "Salary not specified"

class JobSkill(models.Model):
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='required_skills')
    name = models.CharField(max_length=100)
    is_required = models.BooleanField(default=True)
    years_experience = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ['job', 'name']
        ordering = ['-is_required', 'name']
    
    def __str__(self):
        return f"{self.name} for {self.job.title}"

class JobApplication(models.Model):
    APPLICATION_STATUS = [
        ('pending', 'Pending'),
        ('reviewed', 'Under Review'),
        ('shortlisted', 'Shortlisted'),
        ('interviewed', 'Interviewed'),
        ('rejected', 'Rejected'),
        ('hired', 'Hired'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_applications')
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='pending')
    
    # Application tracking
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Recruiter notes
    recruiter_notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['job', 'applicant']
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['applicant', 'status']),
        ]
    
    def __str__(self):
        return f"{self.applicant.get_full_name()} applied to {self.job.title}"