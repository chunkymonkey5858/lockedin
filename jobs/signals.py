from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import JobApplication, ApplicationStatusHistory

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


@receiver(post_save, sender=JobApplication)
def create_initial_status_history(sender, instance, created, **kwargs):
    """Create initial status history when application is created"""
    if created:
        ApplicationStatusHistory.objects.create(
            application=instance,
            status=instance.status,
            changed_by=instance.applicant,
            notes='Application created'
        )


@receiver(pre_save, sender=JobApplication)
def track_status_change(sender, instance, **kwargs):
    """Record a history entry whenever status changes"""
    if not instance.pk:
        return
    try:
        previous = JobApplication.objects.get(pk=instance.pk)
    except JobApplication.DoesNotExist:
        return
    if previous.status != instance.status:
        # Try to infer user from a threadlocal if available; fallback to None
        changed_by = getattr(instance, '_changed_by', None)
        ApplicationStatusHistory.objects.create(
            application=instance,
            status=instance.status,
            changed_by=changed_by,
            notes=f'Status changed from {previous.status} to {instance.status}'
        )
