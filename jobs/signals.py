from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import JobApplication

@receiver(post_save, sender=JobApplication)
def update_application_count_on_create(sender, instance, created, **kwargs):
    """Update job application count when a new application is created"""
    if created:
        job = instance.job
        job.application_count += 1
        job.save(update_fields=['application_count'])

@receiver(post_delete, sender=JobApplication)
def update_application_count_on_delete(sender, instance, **kwargs):
    """Update job application count when an application is deleted"""
    job = instance.job
    job.application_count = max(0, job.application_count - 1)
    job.save(update_fields=['application_count'])
