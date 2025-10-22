from django import forms
from django.core.exceptions import ValidationError
from .models import JobPosting, JobApplication, JobCategory

class JobPostingForm(forms.ModelForm):
    save_action = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = JobPosting
        fields = [
            'title', 'company', 'location', 'latitude', 'longitude', 'work_location', 'employment_type',
            'experience_level', 'description', 'requirements', 'responsibilities',
            'benefits', 'salary_min', 'salary_max', 'salary_currency', 'salary_period',
            'category', 'application_deadline'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Senior Software Engineer',
                'required': True
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your company name',
                'required': True
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., San Francisco, CA or Remote',
                'required': True
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
            'work_location': forms.Select(attrs={'class': 'form-select'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Describe the role, responsibilities, and what makes this opportunity exciting...',
                'required': True
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'List the required skills, experience, and qualifications...'
            }),
            'responsibilities': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Outline the key responsibilities and daily tasks...'
            }),
            'benefits': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe benefits, perks, and what makes your company great...'
            }),
            'salary_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '50000',
                'step': '0.01',
                'min': '0'
            }),
            'salary_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '80000',
                'step': '0.01',
                'min': '0'
            }),
            'salary_currency': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'salary_period': forms.Select(attrs={'class': 'form-select'}),
            'application_deadline': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        save_action = self.data.get('save_action')
        is_draft = save_action == 'save_draft'
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        
        if salary_min and salary_max and salary_min > salary_max:
            raise ValidationError('Minimum salary cannot be greater than maximum salary.')
        
        # For draft saves, skip required field enforcement
        if is_draft:
            # For drafts, default currency to USD if missing
            if not cleaned_data.get('salary_currency'):
                cleaned_data['salary_currency'] = 'USD'
            return cleaned_data
        
        # Validate salary values are reasonable
        if salary_min and salary_min < 0:
            raise ValidationError('Minimum salary cannot be negative.')
        
        if salary_max and salary_max < 0:
            raise ValidationError('Maximum salary cannot be negative.')
        
        return cleaned_data
    
    def clean_salary_min(self):
        salary_min = self.cleaned_data.get('salary_min')
        if salary_min is not None and salary_min < 0:
            raise ValidationError('Salary must be a positive number.')
        return salary_min
    
    def clean_salary_max(self):
        salary_max = self.cleaned_data.get('salary_max')
        if salary_max is not None and salary_max < 0:
            raise ValidationError('Salary must be a positive number.')
        return salary_max

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['cover_letter', 'resume']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Tell us why you\'re interested in this position...',
                'style': 'min-height: 150px; resize: vertical;'
            }),
            'resume': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
        }
    
    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            # Check file size (5MB limit)
            if resume.size > 5 * 1024 * 1024:
                raise ValidationError('Resume file size cannot exceed 5MB.')
            
            # Check file type
            allowed_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            if resume.content_type not in allowed_types:
                raise ValidationError('Please upload a PDF or Word document.')
        
        return resume

class JobSearchForm(forms.Form):
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search jobs...'})
    )
    category = forms.ModelChoiceField(
        queryset=JobCategory.objects.all(),
        required=False,
        empty_label="All Categories"
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Location...'})
    )
    employment_type = forms.ChoiceField(
        choices=[('', 'All Types')] + JobPosting.EMPLOYMENT_TYPES,
        required=False
    )
    experience_level = forms.ChoiceField(
        choices=[('', 'All Levels')] + JobPosting.EXPERIENCE_LEVELS,
        required=False
    )
