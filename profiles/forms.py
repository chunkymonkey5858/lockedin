from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
<<<<<<< HEAD
from .models import CustomUser, JobSeekerProfile, Skill, Education, WorkExperience, Link, AdminActionLog, Conversation, Message
=======
from .models import CustomUser, JobSeekerProfile, Skill, Education, WorkExperience, Link, AdminActionLog
>>>>>>> 1006d701f30381b457008f6864a47881b413ab68

# Universal registration form that supports both job seekers and recruiters
class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your first name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your last name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'}))
    user_type = forms.ChoiceField(
        choices=CustomUser.USER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='job_seeker',
        help_text="Choose your account type"
    )
    
    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'user_type', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a unique username'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Create a strong password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm your password'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = self.cleaned_data['user_type']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

# Keep the old form for backward compatibility
class JobSeekerRegistrationForm(UserRegistrationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide user_type field and default to job_seeker
        self.fields['user_type'].widget = forms.HiddenInput()
        self.fields['user_type'].initial = 'job_seeker'

class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = ['headline', 'bio', 'location', 'latitude', 'longitude', 'phone', 'website', 'linkedin_url', 
                 'github_url', 'portfolio_url', 'profile_picture', 'is_public']
        widgets = {
            'headline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Software Developer | Python Enthusiast'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell recruiters about yourself, your experience, and what you\'re looking for...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., San Francisco, CA'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 37.7749',
                'step': 'any',
                'min': '-90',
                'max': '90'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., -122.4194',
                'step': 'any',
                'min': '-180',
                'max': '180'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., (555) 123-4567'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourwebsite.com'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/yourprofile'
            }),
            'github_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/yourusername'
            }),
            'portfolio_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourportfolio.com'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name', 'level']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Python, JavaScript, Project Management'
            }),
            'level': forms.Select(attrs={'class': 'form-control'})
        }

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['institution', 'degree', 'field_of_study', 'start_date', 
                 'end_date', 'gpa', 'description']
        widgets = {
            'institution': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., University of California, Berkeley'
            }),
            'degree': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Bachelor of Science'
            }),
            'field_of_study': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Computer Science'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gpa': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '4.0',
                'placeholder': 'e.g., 3.75'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Relevant coursework, achievements, activities...'
            })
        }

class WorkExperienceForm(forms.ModelForm):
    class Meta:
        model = WorkExperience
        fields = ['company', 'position', 'location', 'start_date', 
                 'end_date', 'description']
        widgets = {
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Google Inc.'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Software Engineer Intern'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Mountain View, CA'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your responsibilities and achievements...'
            })
        }

class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ['title', 'url', 'link_type']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., My Portfolio'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'link_type': forms.Select(attrs={'class': 'form-control'})
        }

# Formsets for handling multiple entries
SkillFormSet = inlineformset_factory(
    JobSeekerProfile, Skill, form=SkillForm,
    extra=3, can_delete=True, can_delete_extra=False
)

EducationFormSet = inlineformset_factory(
    JobSeekerProfile, Education, form=EducationForm,
    extra=1, can_delete=True, can_delete_extra=False
)

WorkExperienceFormSet = inlineformset_factory(
    JobSeekerProfile, WorkExperience, form=WorkExperienceForm,
    extra=1, can_delete=True, can_delete_extra=False
)

LinkFormSet = inlineformset_factory(
    JobSeekerProfile, Link, form=LinkForm,
    extra=2, can_delete=True, can_delete_extra=False
)

# Admin forms
class UserSearchForm(forms.Form):
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by username, email, or name...'
        })
    )
    user_type = forms.ChoiceField(
        choices=[('', 'All Roles')] + CustomUser.USER_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + CustomUser.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class UserStatusUpdateForm(forms.Form):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('flagged', 'Flagged'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    reason = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional: Reason for status change...'
        })
    )

class UserRoleUpdateForm(forms.Form):
    ROLE_CHOICES = [
        ('job_seeker', 'Job Seeker'),
        ('recruiter', 'Recruiter'),
    ]
    
    user_type = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    reason = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional: Reason for role change...'
        })
    )

class UserDeleteForm(forms.Form):
    confirm_delete = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    reason = forms.CharField(
        max_length=500,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for permanent deletion (required)...'
        })
    )

class PrivacySettingsForm(forms.ModelForm):
    """Form for managing privacy settings"""

    class Meta:
        from .models import PrivacySettings
        model = PrivacySettings
        fields = [
            'privacy_level',
            'show_full_name', 'show_profile_photo', 'show_email', 'show_phone', 'location_visibility',
            'show_current_employer', 'work_history_visibility', 'show_education', 'show_skills', 'show_resume',
            'searchable_by_recruiters', 'allow_recruiter_messages', 'show_salary_expectations',
            'blocked_companies', 'anonymous_mode', 'notify_on_profile_view'
        ]
        widgets = {
            'privacy_level': forms.Select(attrs={
                'class': 'form-select',
                'id': 'privacyLevelSelect'
            }),
            'show_full_name': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_profile_photo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_phone': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'location_visibility': forms.Select(attrs={'class': 'form-select'}),
            'show_current_employer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'work_history_visibility': forms.Select(attrs={'class': 'form-select'}),
            'show_education': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_skills': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_resume': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'searchable_by_recruiters': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_recruiter_messages': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_salary_expectations': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'blocked_companies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter company names separated by commas (e.g., Company A, Company B, Company C)'
            }),
            'anonymous_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_profile_view': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
<<<<<<< HEAD
        }

class MessageForm(forms.ModelForm):
    """Form for sending messages"""
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Type your message here...',
            'maxlength': 1000
        }),
        max_length=1000,
        help_text='Maximum 1000 characters'
    )
    
    class Meta:
        model = Message
        fields = ['content']
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if content and len(content.strip()) == 0:
            raise forms.ValidationError('Message cannot be empty.')
        return content.strip()

class ConversationForm(forms.ModelForm):
    """Form for starting a new conversation"""
    initial_message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Write your initial message...',
            'maxlength': 1000
        }),
        max_length=1000,
        help_text='Maximum 1000 characters'
    )
    
    class Meta:
        model = Conversation
        fields = ['job_posting']
    
    def __init__(self, *args, **kwargs):
        recruiter = kwargs.pop('recruiter', None)
        super().__init__(*args, **kwargs)
        
        if recruiter:
            # Only show job postings from this recruiter
            self.fields['job_posting'].queryset = recruiter.posted_jobs.filter(is_active=True)
            self.fields['job_posting'].required = False
            self.fields['job_posting'].empty_label = "Select a job (optional)"
    
    def clean_initial_message(self):
        message = self.cleaned_data.get('initial_message')
        if message and len(message.strip()) == 0:
            raise forms.ValidationError('Initial message cannot be empty.')
        return message.strip()
=======
        }
>>>>>>> 1006d701f30381b457008f6864a47881b413ab68
