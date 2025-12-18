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
from PIL import Image
from io import BytesIO
from .api_client import search_movie_tmdb, DEFAULT_API_KEY, DEFAULT_ACCESS_TOKEN


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


def download_poster(poster_path: str, save_path: str, resize_to: Tuple[int, int] = (270, 400)) -> bool:
    """
    Download movie poster image from TMDB and resize it.
    
    Args:
        poster_path: TMDB poster path (e.g., "/abc123.jpg")
        save_path: Local path to save the image
        resize_to: Tuple of (width, height) to resize image to (default: 270x400 for cards)
    
    Returns:
        True if successful, False otherwise
    """
    if not poster_path:
        return False
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # TMDB base image URL
    base_url = "https://image.tmdb.org/t/p/w500"  # w500 = 500px width
    image_url = base_url + poster_path
    
    try:
        response = requests.get(image_url, timeout=10, stream=True)
        if response.status_code == 200:
            # Read image into memory
            image_data = BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                image_data.write(chunk)
            image_data.seek(0)
            
            # Open and resize image
            try:
                img = Image.open(image_data)
                # Convert to RGB if necessary (handles RGBA, P, etc.)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize with high-quality resampling
                img_resized = img.resize(resize_to, Image.Resampling.LANCZOS)
                
                # Save resized image
                img_resized.save(save_path, 'JPEG', quality=85)
                return True
            except Exception as e:
                # If resize fails, try saving original
                try:
                    with open(save_path, 'wb') as f:
                        image_data.seek(0)
                        f.write(image_data.read())
                    return True
                except:
                    return False
        else:
            return False
    except requests.exceptions.RequestException:
        return False
    except Exception:
        return False


def get_image_path(movie_title: str, output_dir: str = "movie_posters") -> str:
    """
    Get the expected file path for a movie poster image.
    
    Args:
        movie_title: Title of the movie
        output_dir: Directory where images are stored
    
    Returns:
        Full path to the expected image file (normalized for OS)
    """
    safe_filename = sanitize_filename(movie_title)
    # Use os.path.normpath to handle path separators correctly
    path = os.path.join(output_dir, f"{safe_filename}.jpg")
    return os.path.normpath(path)


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
    # Create output directory if it doesn't exist (normalize path)
    output_dir = os.path.normpath(output_dir)
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
    
    # Use api_key and access_token if provided, otherwise use defaults
    movie_info = search_movie_tmdb(
        movie_title, 
        api_key=api_key if api_key else DEFAULT_API_KEY,
        access_token=access_token if access_token else DEFAULT_ACCESS_TOKEN
    )
    
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

