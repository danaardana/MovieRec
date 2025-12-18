"""
Image Downloader Utility for Movie Recommendations

This module provides functions to download movie poster images on-demand.
It's designed to be used by the recommendation system to fetch images
for recommended movies that don't have posters yet.
"""

import os
import re
import requests
from typing import Optional, List, Tuple

# Default TMDB API credentials (hardcoded for convenience)
DEFAULT_API_KEY = "4ff9323ed178a760f693d3745ae24950"
DEFAULT_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0ZmY5MzIzZWQxNzhhNzYwZjY5M2QzNzQ1YWUyNDk1MCIsIm5iZiI6MTc2NjA2MDA3MS45NjYsInN1YiI6IjY5NDNmMDI3ZjI3YTQ4Mzg0YWQ1NzZlOCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.hWODLWxle3BW9EBFUaVWHlHjaQs2A7FSlew_QQ6j5KU"


def sanitize_filename(filename: str) -> str:
    """
    Remove invalid characters from filename for Windows compatibility.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename safe for Windows filesystem
    """
    # Remove or replace invalid characters: : < > " | ? * \
    invalid_chars = r'[<>:"|?*\\]'
    filename = re.sub(invalid_chars, '_', filename)
    filename = filename.strip(' .')
    
    # Replace multiple underscores/spaces with single underscore
    filename = re.sub(r'[_\s]+', '_', filename)
    
    # Limit length to avoid filesystem issues
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename


def search_movie_tmdb(movie_title: str, api_key: str = None, access_token: str = None) -> Optional[dict]:
    """
    Search for a movie on TMDB and get poster URL.
    
    Args:
        movie_title: Title of the movie to search
        api_key: TMDB API key (uses default if not provided)
        access_token: TMDB access token (optional)
    
    Returns:
        Dictionary with movie info including poster_path, or None if not found
    """
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
                    'overview': movie.get('overview', '')
                }
        elif response.status_code == 401:
            print(f"  Error: Invalid API key for movie '{movie_title}'")
        else:
            print(f"  Warning: Could not search for '{movie_title}' (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"  Warning: Error searching for '{movie_title}': {e}")
    
    return None


def download_poster(poster_path: str, save_path: str) -> bool:
    """
    Download movie poster image from TMDB.
    
    Args:
        poster_path: TMDB poster path (e.g., "/abc123.jpg")
        save_path: Local path to save the image
    
    Returns:
        True if successful, False otherwise
    """
    if not poster_path:
        return False
    
    # TMDB base image URL
    base_url = "https://image.tmdb.org/t/p/w500"  # w500 = 500px width
    image_url = base_url + poster_path
    
    try:
        response = requests.get(image_url, timeout=10, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        else:
            return False
    except requests.exceptions.RequestException:
        return False


def get_image_path(movie_title: str, output_dir: str = "movie_posters") -> str:
    """
    Get the expected file path for a movie poster image.
    
    Args:
        movie_title: Title of the movie
        output_dir: Directory where images are stored
    
    Returns:
        Full path to the expected image file
    """
    safe_filename = sanitize_filename(movie_title)
    return os.path.join(output_dir, f"{safe_filename}.jpg")


def image_exists(movie_title: str, output_dir: str = "movie_posters") -> bool:
    """
    Check if a movie poster image already exists.
    
    Args:
        movie_title: Title of the movie
        output_dir: Directory where images are stored
    
    Returns:
        True if image exists, False otherwise
    """
    image_path = get_image_path(movie_title, output_dir)
    return os.path.exists(image_path)


def download_movie_image(movie_title: str, output_dir: str = "movie_posters",
                          api_key: str = None, access_token: str = None,
                          verbose: bool = False) -> Optional[str]:
    """
    Download a single movie poster image if it doesn't already exist.
    
    Args:
        movie_title: Title of the movie to download
        output_dir: Directory to save the image
        api_key: TMDB API key (uses default if not provided)
        access_token: TMDB access token (optional)
        verbose: Whether to print progress messages
    
    Returns:
        Path to the downloaded image if successful, None otherwise
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if image already exists
    image_path = get_image_path(movie_title, output_dir)
    if os.path.exists(image_path):
        if verbose:
            print(f"  Image already exists: {image_path}")
        return image_path
    
    # Search for movie on TMDB
    if verbose:
        print(f"  Searching for '{movie_title}'...")
    
    movie_info = search_movie_tmdb(movie_title, api_key, access_token)
    
    if movie_info and movie_info.get('poster_path'):
        # Download poster
        if verbose:
            print(f"  Downloading poster...")
        
        if download_poster(movie_info['poster_path'], image_path):
            if verbose:
                print(f"  [OK] Saved: {image_path}")
            return image_path
        else:
            if verbose:
                print(f"  [FAILED] Could not download image")
    else:
        if verbose:
            print(f"  [NOT FOUND] Poster not found on TMDB")
    
    return None


def download_movie_images_batch(movie_titles: List[str], output_dir: str = "movie_posters",
                                api_key: str = None, access_token: str = None,
                                verbose: bool = True) -> List[Tuple[str, Optional[str]]]:
    """
    Download poster images for multiple movies.
    Only downloads images that don't already exist.
    
    Args:
        movie_titles: List of movie titles to download
        output_dir: Directory to save images
        api_key: TMDB API key (uses default if not provided)
        access_token: TMDB access token (optional)
        verbose: Whether to print progress messages
    
    Returns:
        List of tuples (movie_title, image_path) where image_path is None if download failed
    """
    results = []
    
    if verbose:
        print(f"\nDownloading images for {len(movie_titles)} movies...")
        print(f"Output directory: {os.path.abspath(output_dir)}")
        print("="*80)
    
    for i, movie_title in enumerate(movie_titles, 1):
        if verbose:
            print(f"\n[{i}/{len(movie_titles)}] {movie_title}")
        
        image_path = download_movie_image(
            movie_title,
            output_dir=output_dir,
            api_key=api_key,
            access_token=access_token,
            verbose=verbose
        )
        
        results.append((movie_title, image_path))
    
    if verbose:
        successful = sum(1 for _, path in results if path is not None)
        print("\n" + "="*80)
        print(f"Download complete: {successful}/{len(movie_titles)} images downloaded")
        print("="*80)
    
    return results


def ensure_movie_images(recommendations: List[Tuple[int, str, float]], 
                        output_dir: str = "movie_posters",
                        api_key: str = None, access_token: str = None,
                        verbose: bool = False) -> List[Tuple[int, str, float, Optional[str]]]:
    """
    Ensure that poster images exist for recommended movies.
    Downloads missing images automatically.
    
    This function is designed to be used by the recommendation system.
    
    Args:
        recommendations: List of (movie_id, movie_title, predicted_rating) tuples
        output_dir: Directory where images are stored
        api_key: TMDB API key (uses default if not provided)
        access_token: TMDB access token (optional)
        verbose: Whether to print progress messages
    
    Returns:
        List of (movie_id, movie_title, predicted_rating, image_path) tuples
        where image_path is None if image is not available
    """
    results = []
    
    for movie_id, movie_title, predicted_rating in recommendations:
        # Check if image exists, download if not
        image_path = download_movie_image(
            movie_title,
            output_dir=output_dir,
            api_key=api_key,
            access_token=access_token,
            verbose=verbose
        )
        
        # Return relative path or None
        if image_path:
            # Return relative path from current directory
            rel_path = os.path.relpath(image_path)
            results.append((movie_id, movie_title, predicted_rating, rel_path))
        else:
            results.append((movie_id, movie_title, predicted_rating, None))
    
    return results

