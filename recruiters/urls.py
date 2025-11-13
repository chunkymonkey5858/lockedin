from django.urls import path
from . import views

app_name = 'recruiters'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.recruiter_dashboard, name='dashboard'),
    
    # Candidate search and recommendations
    path('search/', views.search_candidates, name='search_candidates'),
    path('recommendations/', views.candidate_recommendations, name='candidate_recommendations'),
    path('candidates/<int:candidate_id>/', views.candidate_detail, name='candidate_detail'),
    path('candidates/<int:candidate_id>/add-note/', views.add_candidate_note, name='add_candidate_note'),
    
    # Saved searches
    path('saved-searches/', views.saved_searches, name='saved_searches'),
    path('saved-searches/create/', views.create_saved_search, name='create_saved_search'),
    path('saved-searches/<int:search_id>/run/', views.run_saved_search, name='run_saved_search'),
    path('saved-searches/<int:search_id>/delete/', views.delete_saved_search, name='delete_saved_search'),
    
    # Notifications
    path('notifications/', views.notification_history, name='notification_history'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/stats/', views.notification_stats, name='notification_stats'),

    # Application Pipeline (Kanban Board)
    path('pipeline/', views.application_pipeline, name='application_pipeline'),
    path('pipeline/job/<int:job_id>/', views.application_pipeline, name='application_pipeline_job'),
    path('applications/<int:application_id>/update-status/', views.update_application_status_kanban, name='update_application_status_kanban'),

    # Applicant Location Map (Story 18)
    path('applicants/map/', views.applicant_location_map, name='applicant_map'),
]
