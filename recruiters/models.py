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
    
    # Notification settings
    notify_on_new_matches = models.BooleanField(default=True, help_text="Send notifications when new candidates match this search")
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('daily', 'Daily Digest'),
            ('weekly', 'Weekly Digest'),
        ],
        default='daily',
        help_text="How often to send notifications"
    )
    last_notified_at = models.DateTimeField(null=True, blank=True, help_text="Last time notifications were sent")
    last_search_at = models.DateTimeField(null=True, blank=True, help_text="Last time this search was run")
    
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


class SearchMatch(models.Model):
    """Track which candidates matched a saved search"""
    saved_search = models.ForeignKey(SavedSearch, on_delete=models.CASCADE, related_name='matches')
    candidate = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='search_matches')
    matched_at = models.DateTimeField(auto_now_add=True)
    is_new_match = models.BooleanField(default=True, help_text="True if this is a new match since last notification")
    notified = models.BooleanField(default=False, help_text="Whether this match has been included in a notification")
    
    class Meta:
        unique_together = ['saved_search', 'candidate']
        ordering = ['-matched_at']
        indexes = [
            models.Index(fields=['saved_search', 'is_new_match']),
            models.Index(fields=['matched_at']),
        ]
    
    def __str__(self):
        return f"Match: {self.candidate.user.get_full_name()} for {self.saved_search.name}"


class SearchNotification(models.Model):
    """Track notifications sent to recruiters about saved search matches"""
    saved_search = models.ForeignKey(SavedSearch, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('daily', 'Daily Digest'),
            ('weekly', 'Weekly Digest'),
        ],
        help_text="Type of notification sent"
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    matches_count = models.IntegerField(default=0, help_text="Number of new matches included in this notification")
    is_read = models.BooleanField(default=False, help_text="Whether the recruiter has read this notification")
    email_sent = models.BooleanField(default=False, help_text="Whether the email was successfully sent")
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['saved_search', 'is_read']),
            models.Index(fields=['sent_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.saved_search.name} - {self.matches_count} matches"