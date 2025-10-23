from django.core.management.base import BaseCommand
from jobs.models import JobPosting, JobApplication

class Command(BaseCommand):
    help = 'Fixes application count inconsistencies in job postings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.stdout.write('=' * 50)
        
        jobs_with_issues = []
        total_fixed = 0
        
        for job in JobPosting.objects.all():
            actual_count = JobApplication.objects.filter(job=job).count()
            stored_count = job.application_count
            
            if actual_count != stored_count:
                jobs_with_issues.append({
                    'job': job,
                    'actual': actual_count,
                    'stored': stored_count
                })
                
                self.stdout.write(f'Job: {job.title} at {job.company}')
                self.stdout.write(f'  Stored count: {stored_count}')
                self.stdout.write(f'  Actual count: {actual_count}')
                self.stdout.write(f'  Difference: {actual_count - stored_count}')
                
                if not dry_run:
                    job.application_count = actual_count
                    job.save(update_fields=['application_count'])
                    self.stdout.write(self.style.SUCCESS('  ✓ Fixed!'))
                else:
                    self.stdout.write(self.style.WARNING('  Would be fixed'))
                
                self.stdout.write()
                total_fixed += 1
        
        if not jobs_with_issues:
            self.stdout.write(self.style.SUCCESS('✓ All application counts are consistent!'))
        else:
            if dry_run:
                self.stdout.write(self.style.WARNING(f'Would fix {total_fixed} jobs with inconsistent counts.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Fixed {total_fixed} jobs with inconsistent counts.'))
        
        # Show summary statistics
        total_jobs = JobPosting.objects.count()
        total_applications = JobApplication.objects.count()
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('SUMMARY:')
        self.stdout.write(f'Total Jobs: {total_jobs}')
        self.stdout.write(f'Total Applications: {total_applications}')
        self.stdout.write(f'Jobs with Issues: {len(jobs_with_issues)}')
        self.stdout.write(f'Jobs Fixed: {total_fixed}')
