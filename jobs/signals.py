from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.urls import reverse
from .models import JobApplication, ApplicationStatusHistory

@receiver(post_save, sender=JobApplication)
def update_application_count_on_create(sender, instance, created, **kwargs):
    """Update job application count when a new application is created"""
    if created:
        job = instance.job
        job.application_count += 1
        job.save(update_fields=['application_count'])
        
        # Create notification for new application
        from profiles.models import Notification
        Notification.objects.create(
            recipient=instance.applicant,
            notification_type='application_status',
            title=f"Application Submitted: {instance.job.title}",
            message=f"Your application to {instance.job.title} at {instance.job.company} has been received and is under review.",
            link=reverse('my_applications'),
            job_application=instance,
            job_posting=instance.job
        )

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
        
        # Create notification for status change
        from profiles.models import Notification
        status_messages = {
            'pending': 'Your application is under review.',
            'reviewing': 'Your application is being reviewed by the hiring team!',
            'shortlisted': 'Great news! You\'ve been shortlisted for further review.',
            'interview': '🎉 Congratulations! You\'ve been invited for an interview.',
            'offer': '🎊 Amazing! You\'ve received a job offer!',
            'rejected': 'Unfortunately, we won\'t be moving forward with your application at this time.',
            'withdrawn': 'Your application has been withdrawn.'
        }
        
        notification_type = 'interview' if instance.status == 'interview' else \
                           'offer' if instance.status == 'offer' else \
                           'application_status'
        
        Notification.objects.create(
            recipient=instance.applicant,
            notification_type=notification_type,
            title=f"Application Update: {instance.job.title}",
            message=status_messages.get(instance.status, f"Your application status has been updated to {instance.get_status_display()}."),
            link=reverse('my_applications'),
            job_application=instance,
            job_posting=instance.job
        )
