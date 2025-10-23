"""
Management command to check saved searches and send notifications
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from recruiters.models import SavedSearch
from recruiters.search_utils import (
    find_new_matches, 
    should_send_notification, 
    mark_matches_as_notified,
    create_notification_record,
    get_notification_matches
)


class Command(BaseCommand):
    help = 'Check saved searches for new matches and send notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without sending actual emails',
        )
        parser.add_argument(
            '--search-id',
            type=int,
            help='Check only a specific saved search ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        search_id = options.get('search_id')
        
        self.stdout.write('Checking saved searches for new matches...')
        
        # Get active saved searches
        searches = SavedSearch.objects.filter(
            is_active=True,
            notify_on_new_matches=True
        )
        
        if search_id:
            searches = searches.filter(id=search_id)
        
        total_notifications = 0
        
        for search in searches:
            self.stdout.write(f'Checking search: {search.name}')
            
            # Find new matches
            new_matches = find_new_matches(search)
            
            if new_matches:
                self.stdout.write(f'  Found {len(new_matches)} new matches')
                
                # Check if we should send notification
                if should_send_notification(search):
                    self.stdout.write(f'  Sending {search.notification_frequency} notification...')
                    
                    if not dry_run:
                        # Send notification
                        success = self.send_notification(search)
                        
                        if success:
                            # Mark matches as notified
                            mark_matches_as_notified(search, search.notification_frequency)
                            
                            # Create notification record
                            create_notification_record(
                                search, 
                                search.notification_frequency, 
                                len(new_matches),
                                email_sent=True
                            )
                            
                            self.stdout.write(f'  Notification sent successfully')
                            total_notifications += 1
                        else:
                            self.stdout.write(f'  Failed to send notification')
                    else:
                        self.stdout.write(f'  [DRY RUN] Would send notification')
                        total_notifications += 1
                else:
                    self.stdout.write(f'  Notification not due yet')
            else:
                self.stdout.write(f'  No new matches found')
        
        self.stdout.write(
            self.style.SUCCESS(f'Completed. {total_notifications} notifications {"would be " if dry_run else ""}sent.')
        )

    def send_notification(self, saved_search):
        """
        Send email notification for new matches
        """
        try:
            # Get new matches
            matches = get_notification_matches(saved_search)
            
            if not matches.exists():
                return False
            
            # Prepare email context
            context = {
                'saved_search': saved_search,
                'matches': matches,
                'matches_count': matches.count(),
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
            }
            
            # Render email templates
            subject = f'New candidates match your search: {saved_search.name}'
            
            if saved_search.notification_frequency == 'immediate':
                template = 'recruiters/emails/new_matches_immediate.html'
            elif saved_search.notification_frequency == 'daily':
                template = 'recruiters/emails/daily_digest.html'
            else:  # weekly
                template = 'recruiters/emails/weekly_digest.html'
            
            html_message = render_to_string(template, context)
            
            # Send email
            send_mail(
                subject=subject,
                message='',  # We're using HTML
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[saved_search.recruiter.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            self.stdout.write(f'Error sending notification: {str(e)}')
            return False
