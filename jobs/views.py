from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import JobPosting, JobCategory, JobApplication, JobSkill
from .forms import JobPostingForm, JobApplicationForm

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