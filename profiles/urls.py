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

    # Privacy settings
    path('privacy-settings/', views.privacy_settings, name='privacy_settings'),
    path('profile/preview/', views.preview_profile, name='preview_profile'),
    
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
    path('my-drafts/', views.my_drafts, name='my_drafts'),
    path('job-applications/<int:job_id>/', views.job_applications, name='job_applications'),
    path('update-application-status/<int:application_id>/', views.update_application_status, name='update_application_status'),
    path('publish-job/<int:job_id>/', views.publish_job, name='publish_job'),
    path('unpublish-job/<int:job_id>/', views.unpublish_job, name='unpublish_job'),
    
    # Admin URLs (using 'dashboard' prefix to avoid conflict with Django admin)
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/action-logs/', views.admin_action_logs, name='admin_action_logs'),
    path('dashboard/update-user-status/<int:user_id>/', views.admin_update_user_status, name='admin_update_user_status'),
    path('dashboard/update-user-role/<int:user_id>/', views.admin_update_user_role, name='admin_update_user_role'),
    path('dashboard/delete-user/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('dashboard/export/<str:data_type>/', views.export_data_csv, name='admin_export_csv'),

    # Messaging URLs
    path('conversations/', views.conversations_list, name='conversations_list'),
    path('conversations/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('conversations/start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('conversations/<int:conversation_id>/send-message/', views.send_message_ajax, name='send_message_ajax'),
    path('conversations/<int:conversation_id>/mark-read/', views.mark_messages_read, name='mark_messages_read'),
    path('messages/count/', views.get_unread_messages_count, name='get_unread_messages_count'),
    path('messages/delete/<int:message_id>/', views.delete_message, name='delete_message'),

    # Notification URLs
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/count/', views.get_unread_notification_count, name='get_unread_notification_count'),

]



