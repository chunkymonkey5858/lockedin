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
    
    # Public profile browsing - THIS LINE WAS MISSING
    path('profiles/', views.public_profile_list, name='profile_list'),
    path('custom-logout/', views.custom_logout, name='custom_logout'),

]



