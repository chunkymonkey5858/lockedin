from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from .models import CustomUser, JobSeekerProfile, Skill, Education, WorkExperience, Link, AdminActionLog

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
        fields = ['headline', 'bio', 'location', 'phone', 'website', 'linkedin_url', 
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