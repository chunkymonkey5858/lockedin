"""
Utility functions for location-based features
"""
import requests
import json
from django.conf import settings

def geocode_address(address):
    """
    Convert an address to latitude and longitude coordinates.
    This is a basic implementation that can be extended with real geocoding services.
    
    Args:
        address (str): The address to geocode
        
    Returns:
        tuple: (latitude, longitude) or (None, None) if geocoding fails
    """
    if not address or not address.strip():
        return None, None
    
    # For now, return None to indicate geocoding is not implemented
    # In a real implementation, you would use a service like:
    # - Google Maps Geocoding API
    # - OpenStreetMap Nominatim
    # - MapBox Geocoding API
    
    # Example implementation with a free service (Nominatim):
    try:
        # This is a placeholder - you would need to implement actual geocoding
        # For now, we'll return None to indicate coordinates need to be entered manually
        return None, None
    except Exception:
        return None, None

def get_user_location_from_profile(user):
    """
    Get the user's location coordinates from their profile.
    
    Args:
        user: The user object
        
    Returns:
        tuple: (latitude, longitude) or (None, None) if not available
    """
    if hasattr(user, 'job_seeker_profile'):
        profile = user.job_seeker_profile
        if profile.latitude and profile.longitude:
            return float(profile.latitude), float(profile.longitude)
    
    return None, None

def get_user_location_from_request(request):
    """
    Get the user's location from request parameters or profile.
    
    Args:
        request: The HTTP request object
        
    Returns:
        tuple: (latitude, longitude) or (None, None) if not available
    """
    # First try to get from request parameters
    user_lat = request.GET.get('user_lat')
    user_lon = request.GET.get('user_lon')
    
    if user_lat and user_lon:
        try:
            return float(user_lat), float(user_lon)
        except (ValueError, TypeError):
            pass
    
    # If not in request, try to get from user profile
    if request.user.is_authenticated:
        return get_user_location_from_profile(request.user)
    
    return None, None
