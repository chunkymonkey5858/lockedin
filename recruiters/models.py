from django.db import models
from django.contrib.auth import get_user_model
from profiles.models import JobSeekerProfile, Skill

User = get_user_model()

class RecruiterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recruiter_profile')
    company = models.CharField(max_length=200)
    title = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=1000, blank=True)
    location = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    profile_picture = models.ImageField(upload_to='recruiter_pictures/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.company}"

class SavedSearch(models.Model):
    recruiter = models.ForeignKey(RecruiterProfile, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Search criteria
    skills = models.ManyToManyField(Skill, blank=True, related_name='saved_searches')
    location = models.CharField(max_length=100, blank=True)
    experience_level = models.CharField(max_length=20, blank=True, choices=[
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive'),
    ])
    employment_type = models.CharField(max_length=20, blank=True, choices=[
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
    ])
    
    # Search preferences
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} by {self.recruiter.user.get_full_name()}"

class CandidateNote(models.Model):
    recruiter = models.ForeignKey(RecruiterProfile, on_delete=models.CASCADE, related_name='candidate_notes')
    candidate = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='recruiter_notes')
    note = models.TextField()
    is_private = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['recruiter', 'candidate']
    
    def __str__(self):
        return f"Note about {self.candidate.user.get_full_name()} by {self.recruiter.user.get_full_name()}"