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
]
