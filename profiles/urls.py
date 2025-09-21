# urls.py (for your app)
from django.urls import path
from . import views

urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    
    # Profile creation and registration
    path('create-professional-profile/', views.create_professional_profile, name='create_professional_profile'),
    path('register/', views.register_redirect, name='register'),  # Redirects to create_professional_profile
    path('register-job-seeker/', views.register_job_seeker, name='register_job_seeker'),  # Redirects to create_professional_profile
    
    # Profile management
    path('profile/create/', views.create_profile, name='create_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/', views.view_profile, name='view_profile'),
    path('profile/<int:user_id>/', views.view_profile, name='view_public_profile'),
    path('profile/delete/', views.delete_profile, name='delete_profile'),
    path('profile/toggle-visibility/', views.toggle_profile_visibility, name='toggle_profile_visibility'),
    
    # Public profile browsing
    path('profiles/', views.public_profile_list, name='profile_list'),
    path('custom-logout/', views.custom_logout, name='custom_logout'),
    
    # Job-related URLs
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/apply/', views.one_click_apply, name='one_click_apply'),
    path('my-applications/', views.my_applications, name='my_applications'),
    
    # Recruiter URLs
    path('post-job/', views.post_job, name='post_job'),
    path('my-jobs/', views.my_job_postings, name='my_job_postings'),
    path('job-applications/<int:job_id>/', views.job_applications, name='job_applications'),
    path('update-application-status/<int:application_id>/', views.update_application_status, name='update_application_status'),
    
    # Admin URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/action-logs/', views.admin_action_logs, name='admin_action_logs'),
    path('admin/update-user-status/<int:user_id>/', views.admin_update_user_status, name='admin_update_user_status'),
    path('admin/update-user-role/<int:user_id>/', views.admin_update_user_role, name='admin_update_user_role'),
    path('admin/delete-user/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),

]



