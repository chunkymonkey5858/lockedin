from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import CustomUser, JobSeekerProfile
from .forms import (
    UserRegistrationForm, JobSeekerRegistrationForm, JobSeekerProfileForm, 
    SkillFormSet, EducationFormSet, WorkExperienceFormSet, LinkFormSet
)

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