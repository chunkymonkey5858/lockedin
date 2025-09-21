from django.core.management.base import BaseCommand
from django.db import transaction
from profiles.models import CustomUser, JobSeekerProfile
from recruiters.models import RecruiterProfile


class Command(BaseCommand):
    help = 'Create missing profiles for users who don\'t have them'

    def handle(self, *args, **options):
        created_count = 0
        
        with transaction.atomic():
            # Check for recruiters without profiles
            recruiters_without_profiles = CustomUser.objects.filter(
                user_type='recruiter'
            ).exclude(
                id__in=RecruiterProfile.objects.values_list('user_id', flat=True)
            )
            
            for user in recruiters_without_profiles:
                RecruiterProfile.objects.create(
                    user=user,
                    company='',
                    title='',
                    bio=''
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created RecruiterProfile for {user.username}')
                )
            
            # Check for job seekers without profiles
            job_seekers_without_profiles = CustomUser.objects.filter(
                user_type='job_seeker'
            ).exclude(
                id__in=JobSeekerProfile.objects.values_list('user_id', flat=True)
            )
            
            for user in job_seekers_without_profiles:
                JobSeekerProfile.objects.create(
                    user=user,
                    headline='Looking for opportunities',
                    bio='',
                    location=''
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created JobSeekerProfile for {user.username}')
                )
        
        if created_count == 0:
            self.stdout.write(
                self.style.SUCCESS('All users already have profiles!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} missing profiles')
            )
