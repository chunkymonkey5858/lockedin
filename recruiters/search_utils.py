"""
Utility functions for saved search notifications
"""
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from profiles.models import JobSeekerProfile
from .models import SavedSearch, SearchMatch, SearchNotification


def run_search_query(saved_search):
    """
    Run a saved search query and return matching candidates
    """
    candidates = JobSeekerProfile.objects.filter(
        is_public=True
    ).select_related('user').prefetch_related('skills', 'work_experience', 'education')
    
    # Apply search criteria
    if saved_search.skills.exists():
        skill_filters = Q()
        for skill in saved_search.skills.all():
            skill_filters |= Q(skills__name__icontains=skill.name)
        candidates = candidates.filter(skill_filters).distinct()
    
    if saved_search.location:
        candidates = candidates.filter(location__icontains=saved_search.location)
    
    if saved_search.experience_level:
        if saved_search.experience_level == 'entry':
            candidates = candidates.filter(work_experience__isnull=True).distinct()
        elif saved_search.experience_level in ['mid', 'senior', 'executive']:
            candidates = candidates.filter(work_experience__isnull=False).distinct()
    
    if saved_search.employment_type:
        # This would need to be implemented based on candidate preferences
        # For now, we'll skip this filter
        pass
    
    return candidates


def find_new_matches(saved_search):
    """
    Find new candidates that match a saved search since the last notification
    """
    # Get current candidates matching search criteria
    current_matches = run_search_query(saved_search)
    
    # Get previously matched candidates
    previous_matches = SearchMatch.objects.filter(
        saved_search=saved_search
    ).values_list('candidate_id', flat=True)
    
    # Find new matches
    new_candidates = current_matches.exclude(id__in=previous_matches)
    
    # Create SearchMatch records for new candidates
    new_matches = []
    for candidate in new_candidates:
        match, created = SearchMatch.objects.get_or_create(
            saved_search=saved_search,
            candidate=candidate,
            defaults={'is_new_match': True, 'notified': False}
        )
        if created:
            new_matches.append(match)
    
    return new_matches


def should_send_notification(saved_search):
    """
    Determine if a notification should be sent for a saved search
    """
    if not saved_search.notify_on_new_matches or not saved_search.is_active:
        return False
    
    # Check if there are new matches
    new_matches = SearchMatch.objects.filter(
        saved_search=saved_search,
        is_new_match=True,
        notified=False
    )
    
    if not new_matches.exists():
        return False
    
    # Check notification frequency
    now = timezone.now()
    
    if saved_search.notification_frequency == 'immediate':
        return True
    elif saved_search.notification_frequency == 'daily':
        if not saved_search.last_notified_at:
            return True
        return (now - saved_search.last_notified_at).days >= 1
    elif saved_search.notification_frequency == 'weekly':
        if not saved_search.last_notified_at:
            return True
        return (now - saved_search.last_notified_at).days >= 7
    
    return False


def mark_matches_as_notified(saved_search, notification_type='immediate'):
    """
    Mark matches as notified and update the saved search
    """
    # Mark all new matches as notified
    SearchMatch.objects.filter(
        saved_search=saved_search,
        is_new_match=True,
        notified=False
    ).update(notified=True, is_new_match=False)
    
    # Update saved search timestamp
    saved_search.last_notified_at = timezone.now()
    saved_search.save(update_fields=['last_notified_at'])


def create_notification_record(saved_search, notification_type, matches_count, email_sent=False):
    """
    Create a notification record for tracking
    """
    return SearchNotification.objects.create(
        saved_search=saved_search,
        notification_type=notification_type,
        matches_count=matches_count,
        email_sent=email_sent
    )


def get_notification_matches(saved_search):
    """
    Get all new matches that should be included in a notification
    """
    return SearchMatch.objects.filter(
        saved_search=saved_search,
        is_new_match=True,
        notified=False
    ).select_related('candidate').order_by('-matched_at')
