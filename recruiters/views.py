from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from profiles.models import JobSeekerProfile, Skill, WorkExperience, Education
<<<<<<< HEAD
from jobs.models import JobPosting, JobSkill, JobApplication
=======
from jobs.models import JobPosting, JobSkill
>>>>>>> 1006d701f30381b457008f6864a47881b413ab68
from .models import RecruiterProfile, SavedSearch, CandidateNote, SearchNotification
from .forms import CandidateSearchForm, SavedSearchForm, CandidateNoteForm

@login_required
def recruiter_dashboard(request):
    """Recruiter dashboard"""
    if not hasattr(request.user, 'recruiter_profile'):
        messages.error(request, 'Only recruiters can access this page.')
        return redirect('home')
    
    recruiter = request.user.recruiter_profile
    
    # Get recent activity
    recent_jobs = request.user.posted_jobs.all()[:5]
    recent_searches = recruiter.saved_searches.all()[:5]
    
    context = {
        'recruiter': recruiter,
        'recent_jobs': recent_jobs,
        'recent_searches': recent_searches,
    }
    
    return render(request, 'recruiters/dashboard.html', context)

@login_required
def search_candidates(request):
    """Search for candidates with advanced filtering"""
    if not hasattr(request.user, 'recruiter_profile'):
        messages.error(request, 'Only recruiters can search for candidates.')
        return redirect('home')
    
    candidates = JobSeekerProfile.objects.filter(
        is_public=True
    ).select_related('user').prefetch_related('skills', 'work_experience', 'education')
    
    # Get search parameters
    search_query = request.GET.get('search', '')
    skills = request.GET.getlist('skills')
    location = request.GET.get('location', '')
    experience_level = request.GET.get('experience_level', '')
    education_level = request.GET.get('education_level', '')
    min_experience = request.GET.get('min_experience', '')
    max_experience = request.GET.get('max_experience', '')
    
    # Apply filters
    if search_query:
        candidates = candidates.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(headline__icontains=search_query) |
            Q(bio__icontains=search_query)
        )
    
    if skills:
        # Filter by skills - candidates must have at least one of the specified skills
        skill_filters = Q()
        for skill in skills:
            skill_filters |= Q(skills__name__icontains=skill)
        candidates = candidates.filter(skill_filters).distinct()
    
    if location:
        candidates = candidates.filter(location__icontains=location)
    
    if experience_level:
        # This is a simplified filter - in a real app you'd have more sophisticated logic
        if experience_level == 'entry':
            candidates = candidates.filter(
                work_experience__isnull=True
            ).distinct()
        elif experience_level == 'mid':
            candidates = candidates.filter(
                work_experience__isnull=False
            ).distinct()
        elif experience_level == 'senior':
            candidates = candidates.filter(
                work_experience__isnull=False
            ).distinct()
    
    if education_level:
        candidates = candidates.filter(
            education__degree__icontains=education_level
        ).distinct()
    
    # Pagination
    paginator = Paginator(candidates, 12)
    page_number = request.GET.get('page')
    candidates = paginator.get_page(page_number)
    
    # Get filter options
    all_skills = Skill.objects.values_list('name', flat=True).distinct().order_by('name')
    
    context = {
        'candidates': candidates,
        'all_skills': all_skills,
        'search_query': search_query,
        'selected_skills': skills,
        'selected_location': location,
        'selected_experience_level': experience_level,
        'selected_education_level': education_level,
        'min_experience': min_experience,
        'max_experience': max_experience,
    }
    
    return render(request, 'recruiters/candidate_search.html', context)

@login_required
def candidate_detail(request, candidate_id):
    """View detailed candidate profile"""
    if not hasattr(request.user, 'recruiter_profile'):
        messages.error(request, 'Only recruiters can view candidate details.')
        return redirect('home')
    
    candidate = get_object_or_404(JobSeekerProfile, id=candidate_id, is_public=True)
    
    # Get recruiter's notes about this candidate
    try:
        recruiter_note = CandidateNote.objects.get(
            recruiter=request.user.recruiter_profile,
            candidate=candidate
        )
    except CandidateNote.DoesNotExist:
        recruiter_note = None
    
    context = {
        'candidate': candidate,
        'recruiter_note': recruiter_note,
    }
    
    return render(request, 'recruiters/candidate_detail.html', context)

@login_required
def add_candidate_note(request, candidate_id):
    """Add or update note about a candidate"""
    if not hasattr(request.user, 'recruiter_profile'):
        messages.error(request, 'Only recruiters can add notes.')
        return redirect('home')
    
    candidate = get_object_or_404(JobSeekerProfile, id=candidate_id, is_public=True)
    recruiter = request.user.recruiter_profile
    
    if request.method == 'POST':
        form = CandidateNoteForm(request.POST)
        if form.is_valid():
            note, created = CandidateNote.objects.get_or_create(
                recruiter=recruiter,
                candidate=candidate,
                defaults={'note': form.cleaned_data['note']}
            )
            if not created:
                note.note = form.cleaned_data['note']
                note.save()
            
            messages.success(request, 'Note saved successfully!')
            return redirect('candidate_detail', candidate_id=candidate_id)
    else:
        # Try to get existing note
        try:
            existing_note = CandidateNote.objects.get(
                recruiter=recruiter,
                candidate=candidate
            )
            form = CandidateNoteForm(initial={'note': existing_note.note})
        except CandidateNote.DoesNotExist:
            form = CandidateNoteForm()
    
    context = {
        'candidate': candidate,
        'form': form,
    }
    
    return render(request, 'recruiters/add_note.html', context)

@login_required
def saved_searches(request):
    """Manage saved searches"""
    if not hasattr(request.user, 'recruiter_profile'):
        messages.error(request, 'Only recruiters can manage saved searches.')
        return redirect('home')
    
    searches = request.user.recruiter_profile.saved_searches.all()
    
    context = {
        'searches': searches,
    }
    
    return render(request, 'recruiters/saved_searches.html', context)

@login_required
def create_saved_search(request):
    """Create a new saved search"""
    if not hasattr(request.user, 'recruiter_profile'):
        messages.error(request, 'Only recruiters can create saved searches.')
        return redirect('home')
    
    if request.method == 'POST':
        form = SavedSearchForm(request.POST)
        if form.is_valid():
            search = form.save(commit=False)
            search.recruiter = request.user.recruiter_profile
            search.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, 'Saved search created successfully!')
            return redirect('saved_searches')
    else:
        form = SavedSearchForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'recruiters/create_saved_search.html', context)

@login_required
def run_saved_search(request, search_id):
    """Run a saved search"""
    if not hasattr(request.user, 'recruiter_profile'):
        messages.error(request, 'Only recruiters can run saved searches.')
        return redirect('home')
    
    search = get_object_or_404(SavedSearch, id=search_id, recruiter=request.user.recruiter_profile)
    
    # Build query based on saved search criteria
    candidates = JobSeekerProfile.objects.filter(is_public=True)
    
    if search.skills.exists():
        skill_filters = Q()
        for skill in search.skills.all():
            skill_filters |= Q(skills__name__icontains=skill.name)
        candidates = candidates.filter(skill_filters).distinct()
    
    if search.location:
        candidates = candidates.filter(location__icontains=search.location)
    
    if search.experience_level:
        # Simplified logic - in production you'd have more sophisticated matching
        if search.experience_level == 'entry':
            candidates = candidates.filter(work_experience__isnull=True).distinct()
        else:
            candidates = candidates.filter(work_experience__isnull=False).distinct()
    
    if search.employment_type:
        # This would need to be implemented based on candidate preferences
        pass
    
    # Pagination
    paginator = Paginator(candidates, 12)
    page_number = request.GET.get('page')
    candidates = paginator.get_page(page_number)
    
    context = {
        'search': search,
        'candidates': candidates,
    }
    
    return render(request, 'recruiters/saved_search_results.html', context)

@login_required
def delete_saved_search(request, search_id):
    """Delete a saved search"""
    if not hasattr(request.user, 'recruiter_profile'):
        messages.error(request, 'Only recruiters can delete saved searches.')
        return redirect('home')
    
    search = get_object_or_404(SavedSearch, id=search_id, recruiter=request.user.recruiter_profile)
    
    if request.method == 'POST':
        search.delete()
        messages.success(request, 'Saved search deleted successfully!')
        return redirect('saved_searches')
    
    context = {
        'search': search,
    }
    
    return render(request, 'recruiters/delete_saved_search.html', context)

@login_required
def candidate_recommendations(request):
    """Recommend candidates based on recruiter's job postings"""
    # Only for recruiters
    if not hasattr(request.user, 'recruiter_profile'):
        messages.error(request, 'Candidate recommendations are only available for recruiters.')
        return redirect('home')
    
    recruiter = request.user.recruiter_profile
    
    # Get recruiter's active job postings
    recruiter_jobs = JobPosting.objects.filter(
        posted_by=request.user,
        is_active=True,
        status='published'
    ).prefetch_related('required_skills')
    
    if not recruiter_jobs.exists():
        messages.info(request, 'Post some job openings to get candidate recommendations!')
        context = {
            'recommended_candidates': [],
            'recruiter_jobs': [],
            'skill_match_info': {},
            'recommendation_type': 'no_jobs'
        }
        return render(request, 'recruiters/candidate_recommendations.html', context)
    
    # Collect all required skills from recruiter's job postings
    all_job_skills = set()
    job_skills_map = {}
    
    for job in recruiter_jobs:
        job_skills = list(job.required_skills.values_list('name', flat=True))
        job_skills_map[job.id] = job_skills
        all_job_skills.update(job_skills)
    
    if not all_job_skills:
        messages.info(request, 'Add required skills to your job postings to get better candidate recommendations!')
        # Show general candidates
        recommended_candidates = JobSeekerProfile.objects.filter(
            is_public=True
        ).select_related('user').prefetch_related('skills', 'work_experience', 'education')[:10]
        
        context = {
            'recommended_candidates': recommended_candidates,
            'recruiter_jobs': recruiter_jobs,
            'skill_match_info': {},
            'recommendation_type': 'general'
        }
        return render(request, 'recruiters/candidate_recommendations.html', context)
    
    # Get all public job seeker profiles
    all_candidates = JobSeekerProfile.objects.filter(
        is_public=True
    ).select_related('user').prefetch_related('skills', 'work_experience', 'education')
    
    # Calculate skill match scores for each candidate
    candidate_scores = []
    skill_match_info = {}
    
    for candidate in all_candidates:
        candidate_skills = list(candidate.skills.values_list('name', flat=True))
        
        if not candidate_skills:
            # Candidates without skills get a low default score
            match_score = 0.1
            matched_skills = []
            missing_skills = list(all_job_skills)
            best_job_match = None
            best_job_score = 0
        else:
            # Calculate matches against all job skills
            matched_skills = []
            for job_skill in all_job_skills:
                for candidate_skill in candidate_skills:
                    if job_skill.lower() == candidate_skill.lower():
                        matched_skills.append(job_skill)
                        break
            
            # Calculate partial matches (substring matching)
            partial_matches = []
            for job_skill in all_job_skills:
                if job_skill not in matched_skills:
                    for candidate_skill in candidate_skills:
                        if (candidate_skill.lower() in job_skill.lower() or 
                            job_skill.lower() in candidate_skill.lower()):
                            partial_matches.append(job_skill)
                            break
            
            # Calculate overall match score
            total_job_skills = len(all_job_skills)
            exact_matches = len(matched_skills)
            partial_match_count = len(partial_matches)
            
            # Scoring: exact matches = 1 point, partial matches = 0.5 points
            match_score = (exact_matches + (partial_match_count * 0.5)) / total_job_skills
            
            # Missing skills
            missing_skills = [skill for skill in all_job_skills 
                            if skill not in matched_skills and skill not in partial_matches]
            
            # Find best matching job for this candidate
            best_job_match = None
            best_job_score = 0
            
            for job in recruiter_jobs:
                job_skills = job_skills_map[job.id]
                if not job_skills:
                    continue
                    
                job_matched = []
                for job_skill in job_skills:
                    for candidate_skill in candidate_skills:
                        if job_skill.lower() == candidate_skill.lower():
                            job_matched.append(job_skill)
                            break
                
                job_score = len(job_matched) / len(job_skills) if job_skills else 0
                if job_score > best_job_score:
                    best_job_score = job_score
                    best_job_match = job
        
        # Store match information
        skill_match_info[candidate.id] = {
            'matched_skills': matched_skills,
            'partial_matches': partial_matches if 'partial_matches' in locals() else [],
            'missing_skills': missing_skills,
            'match_percentage': round(match_score * 100, 1),
            'total_required': len(all_job_skills),
            'best_job_match': best_job_match,
            'best_job_score': round(best_job_score * 100, 1) if best_job_match else 0
        }
        
        candidate_scores.append((candidate, match_score))
    
    # Sort candidates by match score (highest first)
    candidate_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Get top recommendations
    recommended_candidates = [candidate for candidate, score in candidate_scores[:20]]  # Top 20 matches
    
    # Categorize recommendations
    high_match_candidates = [candidate for candidate in recommended_candidates 
                           if skill_match_info[candidate.id]['match_percentage'] >= 70]
    medium_match_candidates = [candidate for candidate in recommended_candidates 
                             if 40 <= skill_match_info[candidate.id]['match_percentage'] < 70]
    potential_candidates = [candidate for candidate in recommended_candidates 
                          if skill_match_info[candidate.id]['match_percentage'] < 40]
    
    context = {
        'recommended_candidates': recommended_candidates,
        'high_match_candidates': high_match_candidates,
        'medium_match_candidates': medium_match_candidates,
        'potential_candidates': potential_candidates,
        'recruiter_jobs': recruiter_jobs,
        'all_job_skills': list(all_job_skills),
        'skill_match_info': skill_match_info,
        'recommendation_type': 'personalized',
        'recruiter': recruiter
    }
    
    return render(request, 'recruiters/candidate_recommendations.html', context)


@login_required
def notification_history(request):
    """View notification history for a recruiter"""
    if not hasattr(request.user, 'recruiter_profile'):
        messages.error(request, 'Only recruiters can access this page.')
        return redirect('home')
    
    recruiter = request.user.recruiter_profile
    
    # Get all notifications for the recruiter's saved searches
    notifications = SearchNotification.objects.filter(
        saved_search__recruiter=recruiter
    ).select_related('saved_search').order_by('-sent_at')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    notifications = paginator.get_page(page_number)
    
    context = {
        'notifications': notifications,
        'recruiter': recruiter,
    }
    
    return render(request, 'recruiters/notification_history.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    if not hasattr(request.user, 'recruiter_profile'):
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    recruiter = request.user.recruiter_profile
    
    try:
        notification = SearchNotification.objects.get(
            id=notification_id,
            saved_search__recruiter=recruiter
        )
        notification.is_read = True
        notification.save()
        
        return JsonResponse({'success': True})
    except SearchNotification.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Notification not found'})


@login_required
def notification_stats(request):
    """Get notification statistics for dashboard"""
    if not hasattr(request.user, 'recruiter_profile'):
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    recruiter = request.user.recruiter_profile
    
    # Get stats for the last 30 days
    from django.utils import timezone
    from datetime import timedelta
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    stats = {
        'total_notifications': SearchNotification.objects.filter(
            saved_search__recruiter=recruiter,
            sent_at__gte=thirty_days_ago
        ).count(),
        'unread_notifications': SearchNotification.objects.filter(
            saved_search__recruiter=recruiter,
            is_read=False
        ).count(),
        'active_searches': SavedSearch.objects.filter(
            recruiter=recruiter,
            is_active=True,
            notify_on_new_matches=True
        ).count(),
    }
    
<<<<<<< HEAD
    return JsonResponse({'success': True, 'stats': stats})

@login_required
def application_pipeline(request, job_id=None):
    """Kanban board view for managing job applications"""
    if not hasattr(request.user, 'recruiter_profile'):
        messages.error(request, 'Only recruiters can access the application pipeline.')
        return redirect('home')
    
    recruiter = request.user.recruiter_profile
    
    # Get recruiter's jobs
    recruiter_jobs = JobPosting.objects.filter(
        posted_by=request.user,
        is_active=True
    ).order_by('-posted_at')
    
    # If specific job is selected, get applications for that job
    selected_job = None
    applications_by_status = {}
    
    if job_id:
        selected_job = get_object_or_404(JobPosting, id=job_id, posted_by=request.user)
        applications = JobApplication.objects.filter(job=selected_job).select_related(
            'applicant', 'applicant__job_seeker_profile'
        ).order_by('-applied_at')
        
        # Group applications by status
        for status_value, status_label in JobApplication.APPLICATION_STATUS:
            applications_by_status[status_value] = {
                'label': status_label,
                'applications': applications.filter(status=status_value)
            }
    else:
        # Get all applications for all recruiter's jobs
        applications = JobApplication.objects.filter(
            job__posted_by=request.user
        ).select_related(
            'applicant', 'applicant__job_seeker_profile', 'job'
        ).order_by('-applied_at')
        
        # Group applications by status
        for status_value, status_label in JobApplication.APPLICATION_STATUS:
            applications_by_status[status_value] = {
                'label': status_label,
                'applications': applications.filter(status=status_value)
            }
    
    context = {
        'recruiter_jobs': recruiter_jobs,
        'selected_job': selected_job,
        'applications_by_status': applications_by_status,
        'status_choices': JobApplication.APPLICATION_STATUS,
    }
    
    return render(request, 'recruiters/application_pipeline.html', context)

@login_required
@require_http_methods(["POST"])
def update_application_status_kanban(request, application_id):
    """Update application status via AJAX for Kanban board"""
    if not hasattr(request.user, 'recruiter_profile'):
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    try:
        application = get_object_or_404(
            JobApplication, 
            id=application_id, 
            job__posted_by=request.user
        )
        
        new_status = request.POST.get('status')
        if new_status not in dict(JobApplication.APPLICATION_STATUS):
            return JsonResponse({'success': False, 'message': 'Invalid status'})
        
        old_status = application.status
        application.status = new_status
        application.save()
        
        # Create status history entry
        from jobs.models import ApplicationStatusHistory
        ApplicationStatusHistory.objects.create(
            application=application,
            status=new_status,
            changed_by=request.user,
            notes=f"Status changed from {dict(JobApplication.APPLICATION_STATUS)[old_status]} to {dict(JobApplication.APPLICATION_STATUS)[new_status]} via Kanban board"
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Application status updated to {dict(JobApplication.APPLICATION_STATUS)[new_status]}',
            'new_status': new_status,
            'new_status_label': dict(JobApplication.APPLICATION_STATUS)[new_status]
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
=======
    return JsonResponse({'success': True, 'stats': stats})
>>>>>>> 1006d701f30381b457008f6864a47881b413ab68
