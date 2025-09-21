from django import forms
from profiles.models import Skill
from .models import SavedSearch, CandidateNote, RecruiterProfile

class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = RecruiterProfile
        fields = [
            'company', 'title', 'bio', 'location', 'phone', 
            'website', 'linkedin_url', 'profile_picture'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

class CandidateSearchForm(forms.Form):
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search candidates...'})
    )
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all().distinct(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select skills to filter by"
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Location...'})
    )
    experience_level = forms.ChoiceField(
        choices=[
            ('', 'All Levels'),
            ('entry', 'Entry Level'),
            ('mid', 'Mid Level'),
            ('senior', 'Senior Level'),
            ('executive', 'Executive'),
        ],
        required=False
    )
    education_level = forms.ChoiceField(
        choices=[
            ('', 'All Education Levels'),
            ('bachelor', 'Bachelor\'s Degree'),
            ('master', 'Master\'s Degree'),
            ('phd', 'PhD'),
            ('associate', 'Associate Degree'),
        ],
        required=False
    )
    min_experience = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'Min years'})
    )
    max_experience = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'Max years'})
    )

class SavedSearchForm(forms.ModelForm):
    class Meta:
        model = SavedSearch
        fields = ['name', 'description', 'skills', 'location', 'experience_level', 'employment_type']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Senior Python Developers'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the type of candidates you are looking for...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., San Francisco, CA or Remote'
            }),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'skills': forms.CheckboxSelectMultiple,
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get all unique skills from the database
        from profiles.models import Skill
        self.fields['skills'].queryset = Skill.objects.all().distinct().order_by('name')

class CandidateNoteForm(forms.ModelForm):
    class Meta:
        model = CandidateNote
        fields = ['note']
        widgets = {
            'note': forms.Textarea(attrs={
                'rows': 6, 
                'placeholder': 'Add your notes about this candidate...',
                'class': 'form-control'
            }),
        }
