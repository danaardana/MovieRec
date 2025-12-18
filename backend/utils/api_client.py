"""
API Client Module

This module handles external API calls, primarily for The Movie Database (TMDB) API.
Used for fetching movie metadata, posters, and overviews.
"""

import requests
from typing import Optional, Dict

# Default TMDB API credentials (hardcoded for convenience)
DEFAULT_API_KEY = "4ff9323ed178a760f693d3745ae24950"
DEFAULT_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0ZmY5MzIzZWQxNzhhNzYwZjY5M2QzNzQ1YWUyNDk1MCIsIm5iZiI6MTc2NjA2MDA3MS45NjYsInN1YiI6IjY5NDNmMDI3ZjI3YTQ4Mzg0YWQ1NzZlOCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.hWODLWxle3BW9EBFUaVWHlHjaQs2A7FSlew_QQ6j5KU"


def search_movie_tmdb(movie_title: str, api_key: str = None, access_token: str = None) -> Optional[Dict]:
    """
    Search for a movie on TMDB and get movie information including poster and overview.
    
    Args:
        movie_title: Title of the movie to search
        api_key: TMDB API key (uses default if not provided)
        access_token: TMDB access token (optional)
    
    Returns:
        Dictionary with movie info including poster_path, overview, release_date, or None if not found
    """
    import re
    
    # Use default API key if not provided
    if not api_key:
        api_key = DEFAULT_API_KEY
    
    # Remove year from title if present (e.g., "Movie (1995)" -> "Movie")
    title_clean = re.sub(r'\s*\(\d{4}\)\s*$', '', movie_title).strip()
    
    # TMDB API endpoint
    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={title_clean}"
    
    try:
        headers = {
            'Accept': 'application/json',
        }
        # Use access token if provided
        if access_token:
            headers['Authorization'] = f'Bearer {access_token}'
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results') and len(data['results']) > 0:
                # Return first result
                movie = data['results'][0]
                return {
                    'title': movie.get('title', title_clean),
                    'poster_path': movie.get('poster_path'),
                    'release_date': movie.get('release_date', ''),
                    'overview': movie.get('overview', ''),
                    'id': movie.get('id')
                }
        elif response.status_code == 401:
            print(f"  Error: Invalid API key for movie '{movie_title}'")
        else:
            print(f"  Warning: Could not search for '{movie_title}' (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"  Warning: Error searching for '{movie_title}': {e}")
    
    return None


def get_movie_overview(movie_title: str, api_key: str = None) -> Optional[str]:
    """
    Get movie overview/description from TMDB API.
    
    Args:
        movie_title: Title of the movie
        api_key: TMDB API key (uses default if not provided)
    
    Returns:
        Movie overview/description string, or None if not found
    """
    movie_info = search_movie_tmdb(movie_title, api_key)
    if movie_info:
        return movie_info.get('overview')
    return None


def get_movie_poster_url(poster_path: str, size: str = 'w500') -> Optional[str]:
    """
    Get full URL for movie poster image.
    
    Args:
        poster_path: TMDB poster path (e.g., "/abc123.jpg")
        size: Image size (w500, w780, original, etc.)
    
    Returns:
        Full URL to the poster image, or None if poster_path is invalid
    """
    if not poster_path:
        return None
    
    base_url = f"https://image.tmdb.org/t/p/{size}"
    return base_url + poster_path

