from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, models
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import CustomUser, JobSeekerProfile, AdminActionLog, PrivacySettings
from .forms import (
    UserRegistrationForm, JobSeekerRegistrationForm, JobSeekerProfileForm,
    SkillFormSet, EducationFormSet, WorkExperienceFormSet, LinkFormSet,
    UserSearchForm, UserStatusUpdateForm, UserRoleUpdateForm, UserDeleteForm,
    PrivacySettingsForm
)
from jobs.models import JobPosting, JobApplication, JobCategory
from jobs.forms import JobPostingForm, JobApplicationForm

def create_professional_profile(request):
    """Create a comprehensive professional profile for new users"""
    if request.user.is_authenticated and hasattr(request.user, 'job_seeker_profile'):
        messages.info(request, 'You already have a professional profile.')
        return redirect('view_profile')
    
    if request.method == 'POST':
        # Handle user registration first
        user_form = UserRegistrationForm(request.POST)
        
        if user_form.is_valid():
            try:
                with transaction.atomic():
                    # Create user
                    user = user_form.save()
                    
                    # Create appropriate profile based on user type
                    if user.user_type == 'recruiter':
                        # Import here to avoid circular imports
                        from recruiters.models import RecruiterProfile
                        RecruiterProfile.objects.create(
                            user=user,
                            company='',
                            title='',
                            bio=''
                        )
                        login(request, user)
                        messages.success(request, 'Recruiter account created successfully! Welcome to LockedIn.')
                        return redirect('recruiters:dashboard')
                    else:
                        # Create job seeker profile (simplified for now)
                        JobSeekerProfile.objects.create(
                            user=user,
                            headline='Looking for opportunities',
                            bio='',
                            location=''
                        )
                        login(request, user)
                        messages.success(request, 'Job seeker account created successfully! Welcome to LockedIn.')
                        return redirect('edit_profile')
                        
            except Exception as e:
                messages.error(request, f'An error occurred while creating your profile: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserRegistrationForm()
        
    # For now, we'll use simplified registration. The full profile form can be filled later.
    profile_form = JobSeekerProfileForm()
    skill_formset = SkillFormSet()
    education_formset = EducationFormSet()
    experience_formset = WorkExperienceFormSet()
    link_formset = LinkFormSet()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'skill_formset': skill_formset,
        'education_formset': education_formset,
        'experience_formset': experience_formset,
        'link_formset': link_formset,
    }
    
    return render(request, 'profiles/create_professional_profile.html', context)

# Keep the old function for backward compatibility
def register_job_seeker(request):
    """Redirect to the new comprehensive profile creation"""
    return redirect('create_professional_profile')

def register_redirect(request):
    """Redirect register URL to create_professional_profile for consistency"""
    return redirect('create_professional_profile')

@login_required
def create_profile(request):
    """Create initial job seeker profile"""
    # Check if profile already exists
    if hasattr(request.user, 'job_seeker_profile'):
        messages.info(request, 'You already have a profile. You can edit it below.')
        return redirect('edit_profile')
    
    if request.method == 'POST':
        form = JobSeekerProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Profile created successfully!')
            return redirect('view_profile')
    else:
        form = JobSeekerProfileForm()
    
    return render(request, 'profiles/create_profile.html', {'form': form})

@login_required
def edit_profile(request):
    """Edit job seeker profile with all related information"""
    profile, created = JobSeekerProfile.objects.get_or_create(
        user=request.user,
        defaults={'headline': 'Looking for opportunities'}
    )
    
    if request.method == 'POST':
        form = JobSeekerProfileForm(request.POST, request.FILES, instance=profile)
        skill_formset = SkillFormSet(request.POST, instance=profile)
        education_formset = EducationFormSet(request.POST, instance=profile)
        experience_formset = WorkExperienceFormSet(request.POST, instance=profile)
        link_formset = LinkFormSet(request.POST, instance=profile)
        
        if (form.is_valid() and skill_formset.is_valid() and 
            education_formset.is_valid() and experience_formset.is_valid() and
            link_formset.is_valid()):
            
            try:
                with transaction.atomic():
                    form.save()
                    skill_formset.save()
                    education_formset.save()
                    experience_formset.save()
                    link_formset.save()
                    messages.success(request, 'Profile updated successfully!')
                    return redirect('view_profile')
            except Exception as e:
                messages.error(request, 'An error occurred while saving. Please try again.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = JobSeekerProfileForm(instance=profile)
        skill_formset = SkillFormSet(instance=profile)
        education_formset = EducationFormSet(instance=profile)
        experience_formset = WorkExperienceFormSet(instance=profile)
        link_formset = LinkFormSet(instance=profile)
    
    context = {
        'form': form,
        'skill_formset': skill_formset,
        'education_formset': education_formset,
        'experience_formset': experience_formset,
        'link_formset': link_formset,
        'profile': profile,
    }
    
    return render(request, 'profiles/edit_profile.html', context)

@login_required
def view_profile(request, user_id=None):
    """View user profile (job seeker or recruiter)"""
    if user_id:
        user = get_object_or_404(CustomUser, id=user_id)
        is_own_profile = request.user == user
        
        # Handle different user types
        if user.user_type == 'job_seeker':
            try:
                profile = JobSeekerProfile.objects.get(user=user)
                # Check if profile is public or if it's the user's own profile
                if not profile.is_public and not is_own_profile:
                    messages.error(request, 'This profile is private.')
                    return redirect('profile_list')
            except JobSeekerProfile.DoesNotExist:
                messages.error(request, 'Job seeker profile not found.')
                return redirect('profile_list')
        elif user.user_type == 'recruiter':
            # Redirect recruiters to their dashboard or show a recruiter profile view
            try:
                from recruiters.models import RecruiterProfile
                profile = RecruiterProfile.objects.get(user=user)
                # For now, redirect to recruiter dashboard or show basic info
                if is_own_profile:
                    return redirect('recruiters:dashboard')
                else:
                    # Show basic recruiter info for other users
                    active_jobs_count = user.posted_jobs.filter(is_active=True).count()
                    context = {
                        'user': user,
                        'profile': profile,
                        'is_own_profile': is_own_profile,
                        'is_recruiter': True,
                        'active_jobs_count': active_jobs_count,
                    }
                    return render(request, 'profiles/recruiter_public_profile.html', context)
            except RecruiterProfile.DoesNotExist:
                messages.error(request, f'Recruiter profile not found for {user.username}. Please contact support.')
                return redirect('home')
            except Exception as e:
                messages.error(request, f'An error occurred while loading the profile: {str(e)}')
                return redirect('home')
        else:
            messages.error(request, 'Invalid user type.')
            return redirect('home')
    else:
        # Viewing own profile - redirect based on user type
        if request.user.user_type == 'recruiter':
            return redirect('recruiters:dashboard')
        else:
            try:
                profile = JobSeekerProfile.objects.get(user=request.user)
                is_own_profile = True
            except JobSeekerProfile.DoesNotExist:
                messages.error(request, 'Profile not found. Please create your profile first.')
                return redirect('create_profile')
    
    context = {
        'profile': profile,
        'is_own_profile': is_own_profile,
        'skills': profile.skills.all(),
        'education': profile.education.all(),
        'experience': profile.work_experience.all(),
        'links': profile.links.all(),
    }
    
    return render(request, 'profiles/view_profile.html', context)

def public_profile_list(request):
    """List all public job seeker profiles"""
    profiles = JobSeekerProfile.objects.filter(
        is_public=True
    ).select_related('user').prefetch_related('skills')
    
    context = {
        'profiles': profiles,
    }
    
    return render(request, 'profiles/profile_list.html', context)

@login_required
@require_http_methods(["POST"])
def toggle_profile_visibility(request):
    """Toggle profile public/private status via AJAX"""
    try:
        profile = request.user.job_seeker_profile
        profile.is_public = not profile.is_public
        profile.save()
        
        return JsonResponse({
            'success': True,
            'is_public': profile.is_public,
            'message': f"Profile is now {'public' if profile.is_public else 'private'}"
        })
    except JobSeekerProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Profile not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred'
        })

@login_required
def delete_profile(request):
    """Delete job seeker profile (keep user account)"""
    if request.method == 'POST':
        try:
            profile = request.user.job_seeker_profile
            profile.delete()
            messages.success(request, 'Profile deleted successfully.')
            return redirect('create_profile')
        except JobSeekerProfile.DoesNotExist:
            messages.error(request, 'No profile found to delete.')
    
    return render(request, 'profiles/delete_profile.html')

# Old register function - replaced by create_professional_profile
# def register(request):
#     """Simple registration view with user type selection"""
#     # This function has been replaced by create_professional_profile
#     # which provides a more comprehensive registration experience

def home(request):
    """Home page view"""
    if request.user.is_authenticated and hasattr(request.user, 'job_seeker_profile'):
        # User has a profile, redirect to their profile
        return redirect('view_profile')
    elif request.user.is_authenticated:
        # User is logged in but no profile, redirect to create profile
        return redirect('edit_profile')
    else:
        # Show homepage to anonymous users
        return render(request, 'home.html')


def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

# Job-related views
@login_required
def job_list(request):
    """Display all active job postings with filtering"""
    from jobs.models import JobPosting, JobCategory, JobSkill
    from jobs.utils import get_user_location_from_request
    from django.db.models import Q
    from django.core.paginator import Paginator
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
    
    jobs = JobPosting.objects.filter(is_active=True).select_related('posted_by', 'category').prefetch_related('required_skills').order_by('-posted_at')
    
    # Filtering
    search = request.GET.get('search', '')
    title = request.GET.get('title', '')
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    employment_type = request.GET.get('employment_type', '')
    experience_level = request.GET.get('experience_level', '')
    skills = request.GET.get('skills', '')
    work_location = request.GET.get('work_location', '')
    salary_min = request.GET.get('salary_min', '')
    salary_max = request.GET.get('salary_max', '')
    visa_sponsorship = request.GET.get('visa_sponsorship', '')
    radius = request.GET.get('radius', '')
    user_lat = request.GET.get('user_lat', '')
    user_lon = request.GET.get('user_lon', '')
    
    if search:
        jobs = jobs.filter(
            Q(title__icontains=search) | 
            Q(company__icontains=search) | 
            Q(description__icontains=search)
        )
    
    if title:
        jobs = jobs.filter(title__icontains=title)
    
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
    
    if work_location:
        jobs = jobs.filter(work_location=work_location)
    
    # Salary overlap logic (use USD values directly). A job with range [A, B]
    # overlaps with filter range [C, D] iff A <= D and B >= C.
    # Handle partial inputs gracefully (only C or only D provided).
    from decimal import Decimal, InvalidOperation
    parsed_salary_min = None
    parsed_salary_max = None
    if salary_min:
        try:
            parsed_salary_min = Decimal(salary_min)
        except (InvalidOperation, ValueError):
            parsed_salary_min = None
    if salary_max:
        try:
            parsed_salary_max = Decimal(salary_max)
        except (InvalidOperation, ValueError):
            parsed_salary_max = None

    if parsed_salary_min is not None and parsed_salary_max is not None:
        # Overlap condition with both bounds provided
        jobs = jobs.filter(salary_min__lte=parsed_salary_max, salary_max__gte=parsed_salary_min)
    elif parsed_salary_min is not None:
        # Any job whose max >= C (lower bound)
        jobs = jobs.filter(salary_max__gte=parsed_salary_min)
    elif parsed_salary_max is not None:
        # Any job whose min <= D (upper bound)
        jobs = jobs.filter(salary_min__lte=parsed_salary_max)
    
    if visa_sponsorship == 'true':
        jobs = jobs.filter(visa_sponsorship=True)
    elif visa_sponsorship == 'false':
        jobs = jobs.filter(visa_sponsorship=False)
    
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
                    jobs = JobPosting.objects.filter(id__in=job_ids, is_active=True).order_by('-posted_at')
                else:
                    jobs = JobPosting.objects.none()
                    
            except (ValueError, TypeError):
                # If radius/location parameters are invalid, ignore location filtering
                pass
    
    # Pagination
    paginator = Paginator(jobs, 10)  # 10 jobs per page (5 rows of 2 jobs each)
    page_number = request.GET.get('page')
    jobs = paginator.get_page(page_number)
    
    # Add application status for current user
    if request.user.user_type == 'job_seeker':
        applied_job_ids = JobApplication.objects.filter(
            applicant=request.user
        ).values_list('job_id', flat=True)
        
        for job in jobs:
            job.has_applied = job.id in applied_job_ids
    
    # Get filter options
    categories = JobCategory.objects.all()
    employment_types = JobPosting.EMPLOYMENT_TYPES
    experience_levels = JobPosting.EXPERIENCE_LEVELS
    work_locations = JobPosting.WORK_LOCATIONS
    
    context = {
        'jobs': jobs,
        'user_type': request.user.user_type,
        'categories': categories,
        'employment_types': employment_types,
        'experience_levels': experience_levels,
        'work_locations': work_locations,
        'search': search,
        'selected_title': title,
        'selected_category': category,
        'selected_location': location,
        'selected_employment_type': employment_type,
        'selected_experience_level': experience_level,
        'selected_skills': skills,
        'selected_work_location': work_location,
        'selected_salary_min': salary_min,
        'selected_salary_max': salary_max,
        'selected_visa_sponsorship': visa_sponsorship,
        'selected_radius': radius,
        'user_lat': user_lat,
        'user_lon': user_lon,
    }
    return render(request, 'profiles/job_list.html', context)

@login_required
def job_detail(request, job_id):
    """Display job details with apply button"""
    job = get_object_or_404(JobPosting, id=job_id, is_active=True)
    
    # Check if user has already applied
    has_applied = False
    if request.user.user_type == 'job_seeker':
        has_applied = JobApplication.objects.filter(
            job=job, 
            applicant=request.user
        ).exists()
    
    # Get user profile for one-click apply
    user_profile = None
    if request.user.user_type == 'job_seeker' and hasattr(request.user, 'job_seeker_profile'):
        user_profile = request.user.job_seeker_profile
    
    context = {
        'job': job,
        'has_applied': has_applied,
        'user_profile': user_profile,
        'user_type': request.user.user_type
    }
    return render(request, 'profiles/job_detail.html', context)

@login_required
@require_http_methods(["POST"])
def one_click_apply(request, job_id):
    """Handle one-click job application"""
    job = get_object_or_404(JobPosting, id=job_id, is_active=True)
    
    # Check if user is a job seeker
    if request.user.user_type != 'job_seeker':
        return JsonResponse({
            'success': False,
            'message': 'Only job seekers can apply to jobs.'
        })
    
    # Check if user already applied
    if JobApplication.objects.filter(job=job, applicant=request.user).exists():
        return JsonResponse({
            'success': False,
            'message': 'You have already applied to this job.'
        })
    
    # Check if user has a complete profile
    if not hasattr(request.user, 'job_seeker_profile'):
        return JsonResponse({
            'success': False,
            'message': 'Please complete your profile before applying.'
        })
    
    try:
        # Create application (application count will be updated automatically via signals)
        application = JobApplication.objects.create(
            job=job,
            applicant=request.user,
            cover_letter=request.POST.get('cover_letter', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Application submitted successfully!',
            'application_id': application.id
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while submitting your application.'
        })

@login_required
def my_applications(request):
    """Display user's job applications"""
    if request.user.user_type != 'job_seeker':
        messages.error(request, 'Only job seekers can view applications.')
        return redirect('home')
    
    applications = JobApplication.objects.filter(
        applicant=request.user
    ).select_related('job', 'job__posted_by').order_by('-applied_at')
    
    # Precompute simple stats for the template to avoid complex template logic
    total_applications = applications.count()
    count_applied = applications.filter(status='applied').count()
    count_interview = applications.filter(status='interview').count()
    count_accepted = applications.filter(outcome='accepted').count()
    
    return render(request, 'profiles/my_applications.html', {
        'applications': applications,
        'total_applications': total_applications,
        'count_applied': count_applied,
        'count_interview': count_interview,
        'count_accepted': count_accepted,
    })

# Recruiter views
@login_required
def post_job(request):
    """Allow recruiters to post new jobs"""
    if request.user.user_type != 'recruiter':
        messages.error(request, 'Only recruiters can post jobs.')
        return redirect('home')
    
    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            save_action = request.POST.get('save_action')
            if save_action == 'save_draft':
                job.status = 'draft'
                job.is_active = False
            else:
                job.status = 'published'
                job.is_active = True
            job.save()
            if job.status == 'draft':
                messages.success(request, 'Draft saved. You can continue editing from My Jobs before publishing.')
                return redirect('my_job_postings')
            messages.success(request, 'Job posted successfully!')
            return redirect('my_job_postings')
        else:
            # Surface validation messages so you can see what's blocking submission
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = JobPostingForm()
    
    return render(request, 'profiles/post_job.html', {'form': form})

@login_required
def my_job_postings(request):
    """Display recruiter's job postings"""
    if request.user.user_type != 'recruiter':
        messages.error(request, 'Only recruiters can view job postings.')
        return redirect('home')

    jobs = JobPosting.objects.filter(posted_by=request.user).order_by('-posted_at')

    return render(request, 'profiles/my_job_postings.html', {
        'jobs': jobs
    })

@login_required
def my_drafts(request):
    """Display recruiter's draft job postings with search and filtering"""
    if request.user.user_type != 'recruiter':
        messages.error(request, 'Only recruiters can view drafts.')
        return redirect('home')

    # Get all drafts for this recruiter
    drafts = JobPosting.objects.filter(posted_by=request.user, status='draft').order_by('-updated_at')

    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        drafts = drafts.filter(
            models.Q(title__icontains=search_query) |
            models.Q(company__icontains=search_query) |
            models.Q(description__icontains=search_query)
        )

    # Filter by location
    location_filter = request.GET.get('location', '').strip()
    if location_filter:
        drafts = drafts.filter(location__icontains=location_filter)

    # Filter by category (department)
    category_filter = request.GET.get('category', '').strip()
    if category_filter:
        drafts = drafts.filter(category__id=category_filter)

    # Sort options
    sort_by = request.GET.get('sort', 'updated')  # Default to last modified
    if sort_by == 'created':
        drafts = drafts.order_by('-posted_at')
    elif sort_by == 'title':
        drafts = drafts.order_by('title')
    else:  # updated
        drafts = drafts.order_by('-updated_at')

    # Get all categories for filter dropdown
    categories = JobCategory.objects.all()

    return render(request, 'profiles/my_drafts.html', {
        'drafts': drafts,
        'categories': categories,
        'search_query': search_query,
        'location_filter': location_filter,
        'category_filter': category_filter,
        'sort_by': sort_by,
    })

@login_required
def publish_job(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id, posted_by=request.user)
    job.status = 'published'
    job.is_active = True
    job.save(update_fields=['status', 'is_active'])
    messages.success(request, 'Job has been published.')
    return redirect('my_job_postings')

@login_required
def unpublish_job(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id, posted_by=request.user)
    job.status = 'draft'
    job.is_active = False
    job.save(update_fields=['status', 'is_active'])
    messages.success(request, 'Job has been moved to draft.')
    return redirect('my_job_postings')

@login_required
def job_applications(request, job_id):
    """Display applications for a specific job"""
    job = get_object_or_404(JobPosting, id=job_id, posted_by=request.user)
    
    applications = JobApplication.objects.filter(
        job=job
    ).select_related('applicant', 'applicant__job_seeker_profile').order_by('-applied_at')
    
    context = {
        'job': job,
        'applications': applications
    }
    return render(request, 'profiles/job_applications.html', context)

@login_required
@require_http_methods(["POST"])
def update_application_status(request, application_id):
    """Update application status via AJAX"""
    application = get_object_or_404(JobApplication, id=application_id)
    
    # Check if user is the recruiter for this job
    if application.job.posted_by != request.user:
        return JsonResponse({
            'success': False,
            'message': 'You are not authorized to update this application.'
        })
    
    try:
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if status in [choice[0] for choice in JobApplication.APPLICATION_STATUS]:
            application.status = status
            application.recruiter_notes = notes
            application.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Application status updated successfully!',
                'new_status': application.get_status_display()
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid status.'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while updating the application.'
        })

# Admin Dashboard Views
def admin_required(view_func):
    """Decorator to ensure only superusers can access admin views"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

def log_admin_action(admin_user, target_user, action_type, description, previous_value='', new_value='', request=None):
    """Helper function to log admin actions"""
    AdminActionLog.objects.create(
        admin_user=admin_user,
        target_user=target_user,
        action_type=action_type,
        description=description,
        previous_value=previous_value,
        new_value=new_value,
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
    )

@admin_required
def admin_dashboard(request):
    """Main admin dashboard with user management"""
    search_form = UserSearchForm(request.GET)
    
    # Get all users with search and filter
    users = CustomUser.objects.all().order_by('-date_joined')
    
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        user_type = search_form.cleaned_data.get('user_type')
        status = search_form.cleaned_data.get('status')
        
        if search:
            users = users.filter(
                models.Q(username__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search)
            )
        
        if user_type:
            users = users.filter(user_type=user_type)
        
        if status:
            users = users.filter(status=status)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(users, 25)  # Show 25 users per page
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    # Statistics
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(status='active').count()
    suspended_users = CustomUser.objects.filter(status='suspended').count()
    flagged_users = CustomUser.objects.filter(status='flagged').count()
    job_seekers = CustomUser.objects.filter(user_type='job_seeker').count()
    recruiters = CustomUser.objects.filter(user_type='recruiter').count()
    
    # Job posting statistics
    from jobs.models import JobPosting
    recent_jobs = JobPosting.objects.filter(is_active=True).order_by('-posted_at')[:10]
    total_jobs = JobPosting.objects.count()
    active_jobs = JobPosting.objects.filter(is_active=True).count()
    inactive_jobs = JobPosting.objects.filter(is_active=False).count()
    
    context = {
        'users': users_page,
        'search_form': search_form,
        'total_users': total_users,
        'active_users': active_users,
        'suspended_users': suspended_users,
        'flagged_users': flagged_users,
        'job_seekers': job_seekers,
        'recruiters': recruiters,
        'recent_jobs': recent_jobs,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'inactive_jobs': inactive_jobs,
    }
    
    return render(request, 'profiles/admin_dashboard.html', context)

@admin_required
@require_http_methods(["POST"])
def admin_update_user_status(request, user_id):
    """Update user status (suspend/reactivate/flag)"""
    try:
        target_user = get_object_or_404(CustomUser, id=user_id)
        
        # Prevent admin from modifying themselves
        if target_user == request.user:
            return JsonResponse({
                'success': False,
                'message': 'You cannot modify your own account status.'
            })
        
        form = UserStatusUpdateForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            reason = form.cleaned_data.get('reason', '')
            
            previous_status = target_user.status
            target_user.status = new_status
            target_user.save()
            
            # Log the action
            description = f"Status changed from {previous_status} to {new_status}"
            if reason:
                description += f". Reason: {reason}"
            
            log_admin_action(
                admin_user=request.user,
                target_user=target_user,
                action_type='suspend' if new_status == 'suspended' else 'reactivate' if new_status == 'active' else 'flag',
                description=description,
                previous_value=previous_status,
                new_value=new_status,
                request=request
            )
            
            return JsonResponse({
                'success': True,
                'message': f'User status updated to {new_status} successfully.',
                'new_status': new_status,
                'new_status_display': target_user.get_status_display()
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid form data.'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while updating user status.'
        })

@admin_required
@require_http_methods(["POST"])
def admin_update_user_role(request, user_id):
    """Update user role (job_seeker/recruiter)"""
    try:
        target_user = get_object_or_404(CustomUser, id=user_id)
        
        # Prevent admin from modifying themselves
        if target_user == request.user:
            return JsonResponse({
                'success': False,
                'message': 'You cannot modify your own account role.'
            })
        
        form = UserRoleUpdateForm(request.POST)
        if form.is_valid():
            new_role = form.cleaned_data['user_type']
            reason = form.cleaned_data.get('reason', '')
            
            previous_role = target_user.user_type
            target_user.user_type = new_role
            target_user.save()
            
            # Log the action
            description = f"Role changed from {previous_role} to {new_role}"
            if reason:
                description += f". Reason: {reason}"
            
            log_admin_action(
                admin_user=request.user,
                target_user=target_user,
                action_type='change_role',
                description=description,
                previous_value=previous_role,
                new_value=new_role,
                request=request
            )
            
            return JsonResponse({
                'success': True,
                'message': f'User role updated to {new_role} successfully.',
                'new_role': new_role,
                'new_role_display': target_user.get_user_type_display()
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid form data.'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while updating user role.'
        })

@admin_required
@require_http_methods(["POST"])
def admin_delete_user(request, user_id):
    """Permanently delete a user account"""
    try:
        target_user = get_object_or_404(CustomUser, id=user_id)
        
        # Prevent admin from deleting themselves
        if target_user == request.user:
            return JsonResponse({
                'success': False,
                'message': 'You cannot delete your own account.'
            })
        
        form = UserDeleteForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            
            # Log the action before deletion
            log_admin_action(
                admin_user=request.user,
                target_user=target_user,
                action_type='delete',
                description=f"User permanently deleted. Reason: {reason}",
                previous_value=f"{target_user.username} ({target_user.email})",
                new_value="DELETED",
                request=request
            )
            
            # Delete the user
            username = target_user.username
            target_user.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'User {username} has been permanently deleted.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Please confirm deletion and provide a reason.'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while deleting the user.'
        })

@admin_required
def admin_action_logs(request):
    """View admin action logs"""
    logs = AdminActionLog.objects.select_related('admin_user', 'target_user').order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)  # Show 50 logs per page
    page_number = request.GET.get('page')
    logs_page = paginator.get_page(page_number)

    context = {
        'logs': logs_page,
    }

    return render(request, 'profiles/admin_action_logs.html', context)

# Privacy Settings Views
@login_required
def privacy_settings(request):
    """Manage privacy settings for job seekers"""
    if request.user.user_type != 'job_seeker':
        messages.error(request, 'Only job seekers can access privacy settings.')
        return redirect('home')

    # Get or create privacy settings for this user's profile
    try:
        profile = request.user.job_seeker_profile
    except JobSeekerProfile.DoesNotExist:
        messages.error(request, 'Please create your profile first.')
        return redirect('create_profile')

    # Get or create privacy settings
    privacy_settings_obj, created = PrivacySettings.objects.get_or_create(profile=profile)

    if request.method == 'POST':
        # Check if a preset was selected
        preset_value = request.POST.get('apply_preset', '').strip()
        if preset_value and preset_value in ['public', 'limited', 'private']:
            privacy_settings_obj.apply_preset(preset_value)
            privacy_settings_obj.save()
            messages.success(request, f'{preset_value.capitalize()} privacy preset applied successfully!')
            return redirect('privacy_settings')

        # Handle form submission
        form = PrivacySettingsForm(request.POST, instance=privacy_settings_obj)
        if form.is_valid():
            updated_settings = form.save(commit=False)
            # If custom selections made, set privacy_level to 'custom'
            if updated_settings.privacy_level != form.initial.get('privacy_level'):
                # User changed preset, apply it
                pass
            else:
                # User manually changed fields, mark as custom
                updated_settings.privacy_level = 'custom'
            updated_settings.save()
            messages.success(request, 'Privacy settings updated successfully!')
            return redirect('privacy_settings')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PrivacySettingsForm(instance=privacy_settings_obj)

    context = {
        'form': form,
        'privacy_settings': privacy_settings_obj,
        'profile': profile,
    }

    return render(request, 'profiles/privacy_settings.html', context)

@login_required
def preview_profile(request):
    """Preview profile as recruiters would see it"""
    if request.user.user_type != 'job_seeker':
        messages.error(request, 'Only job seekers can preview their profile.')
        return redirect('home')

    try:
        profile = request.user.job_seeker_profile
    except JobSeekerProfile.DoesNotExist:
        messages.error(request, 'Please create your profile first.')
        return redirect('create_profile')

    # Get privacy settings
    try:
        privacy_settings_obj = profile.privacy_settings
    except PrivacySettings.DoesNotExist:
        privacy_settings_obj = PrivacySettings.objects.create(profile=profile)

    context = {
        'user_profile': profile,
        'privacy_settings': privacy_settings_obj,
        'is_preview': True,
    }

    return render(request, 'profiles/profile_preview.html', context)