from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Case, When, IntegerField
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import JobPosting, JobCategory, JobApplication, JobSkill
from .forms import JobPostingForm, JobApplicationForm
from .utils import get_user_location_from_request
from profiles.models import JobSeekerProfile, Skill
import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on Earth in miles"""
    if not all([lat1, lon1, lat2, lon2]):
        return None
    
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in miles
    r = 3959
    return c * r

def job_list(request):
    """List all active job postings with filtering"""
    jobs = JobPosting.objects.filter(is_active=True, status='published').select_related('posted_by', 'category').prefetch_related('required_skills')
    
    # Filtering
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    employment_type = request.GET.get('employment_type', '')
    experience_level = request.GET.get('experience_level', '')
    skills = request.GET.get('skills', '')
    radius = request.GET.get('radius', '')
    user_lat = request.GET.get('user_lat', '')
    user_lon = request.GET.get('user_lon', '')
    
    if search:
        jobs = jobs.filter(
            Q(title__icontains=search) | 
            Q(company__icontains=search) | 
            Q(description__icontains=search)
        )
    
    if category:
        jobs = jobs.filter(category__name__icontains=category)
    
    if location:
        jobs = jobs.filter(location__icontains=location)
    
    if employment_type:
        jobs = jobs.filter(employment_type=employment_type)
    
    if experience_level:
        jobs = jobs.filter(experience_level=experience_level)
    
    if skills:
        # Filter jobs that have any of the specified skills
        skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        if skills_list:
            jobs = jobs.filter(required_skills__name__in=skills_list).distinct()
    
    # Location-based filtering with radius
    if radius:
        # Try to get user location from request parameters or profile
        user_lat, user_lon = get_user_location_from_request(request)
        
        if user_lat and user_lon:
            try:
                radius_miles = float(radius)
                
                # Get all jobs first, then filter by distance
                all_jobs = list(jobs)
                jobs_within_radius = []
                
                for job in all_jobs:
                    if job.latitude and job.longitude:
                        distance = calculate_distance(user_lat, user_lon, float(job.latitude), float(job.longitude))
                        if distance is not None and distance <= radius_miles:
                            jobs_within_radius.append(job)
                    else:
                        # If job doesn't have coordinates, include it if location text matches
                        if location and location.lower() in job.location.lower():
                            jobs_within_radius.append(job)
                
                # Create a new queryset with the filtered job IDs
                if jobs_within_radius:
                    job_ids = [job.id for job in jobs_within_radius]
                    jobs = JobPosting.objects.filter(id__in=job_ids, is_active=True, status='published')
                else:
                    jobs = JobPosting.objects.none()
                    
            except (ValueError, TypeError):
                # If radius/location parameters are invalid, ignore location filtering
                pass
    
    # Pagination
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page')
    jobs = paginator.get_page(page_number)
    
    # Get filter options
    categories = JobCategory.objects.all()
    employment_types = JobPosting.EMPLOYMENT_TYPES
    experience_levels = JobPosting.EXPERIENCE_LEVELS
    
    # Get all unique skills for the skills filter dropdown
    all_skills = JobSkill.objects.values_list('name', flat=True).distinct().order_by('name')
    
    context = {
        'jobs': jobs,
        'categories': categories,
        'employment_types': employment_types,
        'experience_levels': experience_levels,
        'all_skills': all_skills,
        'search': search,
        'selected_category': category,
        'selected_location': location,
        'selected_employment_type': employment_type,
        'selected_experience_level': experience_level,
        'selected_skills': skills,
        'selected_radius': radius,
        'user_lat': user_lat,
        'user_lon': user_lon,
    }
    
    return render(request, 'jobs/job_list.html', context)

def job_detail(request, job_id):
    """View job posting details"""
    job = get_object_or_404(JobPosting, id=job_id, is_active=True, status='published')
    
    # Increment view count
    job.view_count += 1
    job.save(update_fields=['view_count'])
    
    # Check if user has applied
    has_applied = False
    if request.user.is_authenticated:
        has_applied = JobApplication.objects.filter(
            job=job, 
            applicant=request.user
        ).exists()
    
    # Get required skills
    required_skills = job.required_skills.all()
    
    context = {
        'job': job,
        'has_applied': has_applied,
        'required_skills': required_skills,
    }
    
    return render(request, 'jobs/job_detail.html', context)

@login_required
def apply_to_job(request, job_id):
    """Apply to a job posting"""
    job = get_object_or_404(JobPosting, id=job_id, is_active=True, status='published')
    
    # Check if user already applied
    if JobApplication.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, 'You have already applied to this job.')
        return redirect('job_detail', job_id=job_id)
    
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()  # Application count will be updated automatically via signals
            
            messages.success(request, 'Your application has been submitted successfully!')
            return redirect('jobs:application_success', job_id=job_id, application_id=application.id)
    else:
        form = JobApplicationForm()
    
    context = {
        'job': job,
        'form': form,
    }
    
    return render(request, 'jobs/apply_to_job.html', context)

@login_required
def application_success(request, job_id, application_id):
    """Application success page"""
    job = get_object_or_404(JobPosting, id=job_id)
    application = get_object_or_404(JobApplication, id=application_id, applicant=request.user, job=job)
    
    context = {
        'job': job,
        'application': application,
    }
    
    return render(request, 'jobs/application_success.html', context)

@login_required
def my_applications(request):
    """View user's job applications"""
    applications = JobApplication.objects.filter(
        applicant=request.user
    ).select_related('job', 'job__posted_by').order_by('-applied_at')
    
    context = {
        'applications': applications,
    }
    
    return render(request, 'jobs/my_applications.html', context)

@login_required
def post_job(request):
    """Create a new job posting (recruiters only)"""
    if not hasattr(request.user, 'recruiter_profile'):
        messages.error(request, 'Only recruiters can post jobs.')
        return redirect('home')
    
    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            try:
                job = form.save(commit=False)
                job.posted_by = request.user
                # Determine save action (draft vs publish)
                save_action = form.cleaned_data.get('save_action') or request.POST.get('save_action')
                if save_action == 'save_draft':
                    job.status = 'draft'
                    job.is_active = False
                else:
                    job.status = 'published'
                    job.is_active = True
                job.save()
                
                # Handle skills - parse comma-separated string
                skills_input = request.POST.get('skills', '')
                if skills_input.strip():
                    skills_list = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
                    for skill_name in skills_list:
                        JobSkill.objects.create(
                            job=job,
                            name=skill_name,
                            is_required=True
                        )
                
                if job.status == 'draft':
                    messages.success(request, 'Draft saved. You can continue editing from My Jobs before publishing.')
                    return redirect('jobs:my_jobs')
                else:
                    messages.success(request, 'Job posted successfully!')
                    return redirect('jobs:job_detail', job_id=job.id)
            except Exception as e:
                messages.error(request, f'Error creating job posting: {str(e)}')
        else:
            # Debug form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = JobPostingForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'jobs/post_job.html', context)

@login_required
def my_jobs(request):
    """View recruiter's posted jobs"""
    if not hasattr(request.user, 'recruiter_profile'):
        messages.error(request, 'Only recruiters can view this page.')
        return redirect('home')
    
    jobs = JobPosting.objects.filter(
        posted_by=request.user
    ).select_related('category').prefetch_related('applications').order_by('-posted_at')
    
    context = {
        'jobs': jobs,
    }
    
    return render(request, 'jobs/my_jobs.html', context)

@login_required
def edit_job(request, job_id):
    """Edit job posting"""
    job = get_object_or_404(JobPosting, id=job_id, posted_by=request.user)

    if request.method == 'POST':
        form = JobPostingForm(request.POST, instance=job)
        if form.is_valid():
            try:
                updated_job = form.save(commit=False)
                # Determine save action (draft vs publish vs save & continue)
                save_action = form.cleaned_data.get('save_action') or request.POST.get('save_action')
                if save_action in ['save_draft', 'save_continue']:
                    updated_job.status = 'draft'
                    updated_job.is_active = False
                else:
                    updated_job.status = 'published'
                    updated_job.is_active = True
                updated_job.save()

                # Handle skills - delete existing and add new ones
                job.required_skills.all().delete()
                skills_input = request.POST.get('skills', '')
                if skills_input.strip():
                    skills_list = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
                    for skill_name in skills_list:
                        JobSkill.objects.create(
                            job=job,
                            name=skill_name,
                            is_required=True
                        )

                if save_action == 'save_continue':
                    messages.success(request, 'Changes saved! You can continue editing.')
                    return redirect('jobs:edit_job', job_id=job_id)
                elif updated_job.status == 'draft':
                    messages.success(request, 'Draft saved successfully!')
                    return redirect('jobs:my_jobs')
                else:
                    messages.success(request, 'Job updated successfully!')
                    return redirect('jobs:job_detail', job_id=job_id)
            except Exception as e:
                messages.error(request, f'Error updating job posting: {str(e)}')
        else:
            # Debug form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = JobPostingForm(instance=job)

    # Get existing skills as comma-separated string
    existing_skills = ', '.join([skill.name for skill in job.required_skills.all()])

    context = {
        'job': job,
        'form': form,
        'existing_skills': existing_skills,
    }

    return render(request, 'jobs/edit_job.html', context)

@login_required
def delete_job(request, job_id):
    """Delete job posting"""
    job = get_object_or_404(JobPosting, id=job_id, posted_by=request.user)
    
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job deleted successfully!')
        return redirect('my_jobs')
    
    context = {
        'job': job,
    }
    
    return render(request, 'jobs/delete_job.html', context)

@login_required
def job_applications(request, job_id):
    """View applications for a specific job"""
    job = get_object_or_404(JobPosting, id=job_id, posted_by=request.user)
    
    applications = JobApplication.objects.filter(
        job=job
    ).select_related('applicant').prefetch_related('status_history').order_by('-applied_at')
    
    context = {
        'job': job,
        'applications': applications,
    }
    
    return render(request, 'jobs/job_applications.html', context)

@login_required
@require_http_methods(["POST"])
def update_application_status(request, application_id):
    """Update application status via AJAX"""
    try:
        application = get_object_or_404(JobApplication, id=application_id)
        
        # Check if user owns the job
        if application.job.posted_by != request.user:
            return JsonResponse({'success': False, 'message': 'Permission denied'})
        
        new_status = request.POST.get('status')
        if new_status in [choice[0] for choice in JobApplication.APPLICATION_STATUS]:
            # Attach user for signals to record who changed it
            application._changed_by = request.user
            application.status = new_status
            application.save()
            
            return JsonResponse({
                'success': True,
                'status': new_status,
                'message': f'Application status updated to {new_status}'
            })
        else:
            return JsonResponse({'success': False, 'message': 'Invalid status'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred'})

@login_required
def job_recommendations(request):
    """Recommend jobs based on user's skills and profile"""
    # Only for job seekers
    if request.user.user_type != 'job_seeker':
        messages.error(request, 'Job recommendations are only available for job seekers.')
        return redirect('home')
    
    # Check if user has a job seeker profile
    try:
        profile = request.user.job_seeker_profile
    except JobSeekerProfile.DoesNotExist:
        messages.error(request, 'Please complete your profile to get job recommendations.')
        return redirect('create_professional_profile')
    
    # Get user's skills
    user_skills = list(profile.skills.values_list('name', flat=True))
    
    if not user_skills:
        messages.info(request, 'Add skills to your profile to get personalized job recommendations.')
        recommended_jobs = JobPosting.objects.filter(
            is_active=True, 
            status='published'
        ).select_related('posted_by', 'category').prefetch_related('required_skills')[:10]
        
        context = {
            'recommended_jobs': recommended_jobs,
            'user_skills': [],
            'skill_match_info': {},
            'recommendation_type': 'general'
        }
        return render(request, 'jobs/job_recommendations.html', context)
    
    # Get all active jobs with their required skills
    all_jobs = JobPosting.objects.filter(
        is_active=True, 
        status='published'
    ).select_related('posted_by', 'category').prefetch_related('required_skills')
    
    # Calculate skill match scores for each job
    job_scores = []
    skill_match_info = {}
    
    for job in all_jobs:
        job_skills = list(job.required_skills.values_list('name', flat=True))
        
        if not job_skills:
            # Jobs without specified skills get a low default score
            match_score = 0.1
            matched_skills = []
            missing_skills = []
        else:
            # Calculate exact matches (case-insensitive)
            matched_skills = []
            for job_skill in job_skills:
                for user_skill in user_skills:
                    if job_skill.lower() == user_skill.lower():
                        matched_skills.append(job_skill)
                        break
            
            # Calculate partial matches (substring matching)
            partial_matches = []
            for job_skill in job_skills:
                if job_skill not in matched_skills:
                    for user_skill in user_skills:
                        if (user_skill.lower() in job_skill.lower() or 
                            job_skill.lower() in user_skill.lower()):
                            partial_matches.append(job_skill)
                            break
            
            # Calculate match score
            total_job_skills = len(job_skills)
            exact_matches = len(matched_skills)
            partial_match_count = len(partial_matches)
            
            # Scoring: exact matches = 1 point, partial matches = 0.5 points
            match_score = (exact_matches + (partial_match_count * 0.5)) / total_job_skills
            
            # Missing skills
            missing_skills = [skill for skill in job_skills 
                            if skill not in matched_skills and skill not in partial_matches]
        
        # Store match information
        skill_match_info[job.id] = {
            'matched_skills': matched_skills,
            'partial_matches': partial_matches if 'partial_matches' in locals() else [],
            'missing_skills': missing_skills,
            'match_percentage': round(match_score * 100, 1),
            'total_required': len(job_skills)
        }
        
        job_scores.append((job, match_score))
    
    # Sort jobs by match score (highest first)
    job_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Get top recommendations
    recommended_jobs = [job for job, score in job_scores[:20]]  # Top 20 matches
    
    # Filter out jobs user has already applied to
    applied_job_ids = JobApplication.objects.filter(
        applicant=request.user
    ).values_list('job_id', flat=True)
    
    recommended_jobs = [job for job in recommended_jobs if job.id not in applied_job_ids][:10]
    
    # Categorize recommendations
    high_match_jobs = [job for job in recommended_jobs 
                      if skill_match_info[job.id]['match_percentage'] >= 70]
    medium_match_jobs = [job for job in recommended_jobs 
                        if 40 <= skill_match_info[job.id]['match_percentage'] < 70]
    potential_jobs = [job for job in recommended_jobs 
                     if skill_match_info[job.id]['match_percentage'] < 40]
    
    context = {
        'recommended_jobs': recommended_jobs,
        'high_match_jobs': high_match_jobs,
        'medium_match_jobs': medium_match_jobs,
        'potential_jobs': potential_jobs,
        'user_skills': user_skills,
        'skill_match_info': skill_match_info,
        'recommendation_type': 'personalized',
        'profile': profile
    }
    
    return render(request, 'jobs/job_recommendations.html', context)

@login_required
def job_map(request):
    """Interactive map view showing all jobs with location filtering"""
    from jobs.utils import get_user_location_from_request

    # Get all active jobs with coordinates
    jobs = JobPosting.objects.filter(
        is_active=True,
        status='published',
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related('posted_by', 'category').prefetch_related('required_skills')

    # Get user's preferred commute radius and location from profile (Story 9)
    user_profile = None
    default_radius = ''
    default_lat = ''
    default_lon = ''

    if hasattr(request.user, 'job_seeker_profile'):
        user_profile = request.user.job_seeker_profile
        if user_profile.commute_radius_miles:
            default_radius = str(user_profile.commute_radius_miles)
        if user_profile.latitude and user_profile.longitude:
            default_lat = str(user_profile.latitude)
            default_lon = str(user_profile.longitude)

    # Get filter parameters (allow override of profile defaults)
    radius = request.GET.get('radius', default_radius)
    user_lat = request.GET.get('user_lat', default_lat)
    user_lon = request.GET.get('user_lon', default_lon)

    # Save updated radius to profile if changed
    if request.GET.get('save_radius') == 'true' and radius and user_profile:
        try:
            user_profile.commute_radius_miles = int(radius)
            user_profile.save()
        except (ValueError, TypeError):
            pass
    location = request.GET.get('location', '')
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    employment_type = request.GET.get('employment_type', '')
    experience_level = request.GET.get('experience_level', '')
    skills = request.GET.get('skills', '')
    
    # Apply text-based filters first
    if search:
        jobs = jobs.filter(
            Q(title__icontains=search) | 
            Q(company__icontains=search) | 
            Q(description__icontains=search)
        )
    
    if category:
        jobs = jobs.filter(category__name__icontains=category)
    
    if location:
        jobs = jobs.filter(location__icontains=location)
    
    if employment_type:
        jobs = jobs.filter(employment_type=employment_type)
    
    if experience_level:
        jobs = jobs.filter(experience_level=experience_level)
    
    if skills:
        skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        if skills_list:
            jobs = jobs.filter(required_skills__name__in=skills_list).distinct()
    
    # Apply location-based filtering with radius
    if radius:
        user_lat, user_lon = get_user_location_from_request(request)
        
        if user_lat and user_lon:
            try:
                radius_miles = float(radius)
                
                # Get all jobs first, then filter by distance
                all_jobs = list(jobs)
                jobs_within_radius = []
                
                for job in all_jobs:
                    if job.latitude and job.longitude:
                        distance = calculate_distance(user_lat, user_lon, float(job.latitude), float(job.longitude))
                        if distance is not None and distance <= radius_miles:
                            jobs_within_radius.append(job)
                    else:
                        # If job doesn't have coordinates, include it if location text matches
                        if location and location.lower() in job.location.lower():
                            jobs_within_radius.append(job)
                
                # Create a new queryset with the filtered job IDs
                if jobs_within_radius:
                    job_ids = [job.id for job in jobs_within_radius]
                    jobs = JobPosting.objects.filter(id__in=job_ids, is_active=True, status='published')
                else:
                    jobs = JobPosting.objects.none()
                    
            except (ValueError, TypeError):
                pass
    
    # Get filter options
    categories = JobCategory.objects.all()
    employment_types = JobPosting.EMPLOYMENT_TYPES
    experience_levels = JobPosting.EXPERIENCE_LEVELS
    
    # Get all unique skills for the skills filter dropdown
    all_skills = JobSkill.objects.values_list('name', flat=True).distinct().order_by('name')
    
    # Prepare job data for the map
    job_markers = []
    for job in jobs:
        job_markers.append({
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'latitude': float(job.latitude),
            'longitude': float(job.longitude),
            'employment_type': job.get_employment_type_display(),
            'experience_level': job.get_experience_level_display(),
            'salary_range': job.salary_range,
            'url': f'/jobs/{job.id}/',
            'description': job.description[:200] + '...' if len(job.description) > 200 else job.description,
        })
    
    context = {
        'jobs': jobs,
        'job_markers': job_markers,
        'categories': categories,
        'employment_types': employment_types,
        'experience_levels': experience_levels,
        'all_skills': all_skills,
        'search': search,
        'selected_category': category,
        'selected_location': location,
        'selected_employment_type': employment_type,
        'selected_experience_level': experience_level,
        'selected_skills': skills,
        'selected_radius': radius,
        'user_lat': user_lat,
        'user_lon': user_lon,
    }
    
    return render(request, 'jobs/job_map.html', context)


# Admin moderation views
def admin_required(view_func):
    """Decorator to require admin access"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, 'You must be an admin to access this page.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_delete_job(request, job_id):
    """Admin can delete a job posting"""
    job = get_object_or_404(JobPosting, id=job_id)
    job_title = job.title
    job.delete()  # Hard delete
    messages.success(request, f'Job "{job_title}" has been permanently deleted.')
    return redirect('profiles:admin_dashboard')


@admin_required
def admin_deactivate_job(request, job_id):
    """Admin can deactivate a job posting"""
    job = get_object_or_404(JobPosting, id=job_id)
    job.is_active = False
    job.save()
    messages.success(request, f'Job "{job.title}" has been deactivated.')
    return redirect('profiles:admin_dashboard')


@admin_required
def admin_activate_job(request, job_id):
    """Admin can reactivate a job posting"""
    job = get_object_or_404(JobPosting, id=job_id)
    job.is_active = True
    job.save()
    messages.success(request, f'Job "{job.title}" has been reactivated.')
    return redirect('profiles:admin_dashboard')