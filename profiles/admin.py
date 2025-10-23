from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, JobSeekerProfile, Skill, Education, WorkExperience, Link

class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff']
    list_filter = ['user_type', 'is_staff', 'is_superuser', 'is_active']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type',)}),
    )

class SkillInline(admin.TabularInline):
    model = Skill
    extra = 3

class EducationInline(admin.TabularInline):
    model = Education
    extra = 1

class WorkExperienceInline(admin.TabularInline):
    model = WorkExperience
    extra = 1

class LinkInline(admin.TabularInline):
    model = Link
    extra = 2

@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'headline', 'location', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'headline', 'location']
    
    inlines = [SkillInline, EducationInline, WorkExperienceInline, LinkInline]

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Skill)
admin.site.register(Education)
admin.site.register(WorkExperience)
admin.site.register(Link)
