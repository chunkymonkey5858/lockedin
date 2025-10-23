from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    # Job listings
    path('', views.job_list, name='job_list'),
    path('<int:job_id>/', views.job_detail, name='job_detail'),
    path('<int:job_id>/apply/', views.apply_to_job, name='apply_to_job'),
    path('<int:job_id>/application/<int:application_id>/success/', views.application_success, name='application_success'),
    
    # Job management (recruiters)
    path('post/', views.post_job, name='post_job'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('<int:job_id>/edit/', views.edit_job, name='edit_job'),
    path('<int:job_id>/delete/', views.delete_job, name='delete_job'),
    path('<int:job_id>/applications/', views.job_applications, name='job_applications'),
    
    # User applications
    path('my-applications/', views.my_applications, name='my_applications'),
    
    # Job recommendations
    path('recommendations/', views.job_recommendations, name='job_recommendations'),
    
    # Interactive map
    path('map/', views.job_map, name='job_map'),
    
    # AJAX endpoints
    path('applications/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
    
    # Admin moderation
    path('admin/delete/<int:job_id>/', views.admin_delete_job, name='admin_delete_job'),
    path('admin/deactivate/<int:job_id>/', views.admin_deactivate_job, name='admin_deactivate_job'),
    path('admin/activate/<int:job_id>/', views.admin_activate_job, name='admin_activate_job'),
]
