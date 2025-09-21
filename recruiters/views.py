from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from profiles.models import JobSeekerProfile, Skill, WorkExperience, Education
from .models import RecruiterProfile, SavedSearch, CandidateNote
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