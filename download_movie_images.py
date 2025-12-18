"""
Script to download movie poster images for top movies.

This script fetches the top movies and downloads their poster images
from The Movie Database (TMDB) API.
"""

import argparse
import sys
import os
import re
import requests
from typing import List, Tuple
from recommender import load_data, get_top_movies

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
    # Also remove leading/trailing spaces and dots
    invalid_chars = r'[<>:"|?*\\]'
    filename = re.sub(invalid_chars, '_', filename)
    filename = filename.strip(' .')
    
    # Replace multiple underscores/spaces with single underscore
    filename = re.sub(r'[_\s]+', '_', filename)
    
    # Limit length to avoid filesystem issues
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename


def search_movie_tmdb(movie_title: str, api_key: str = None, access_token: str = None) -> dict:
    """
    Search for a movie on TMDB and get poster URL.
    
    Args:
        movie_title: Title of the movie to search
        api_key: TMDB API key (uses default if not provided)
        access_token: TMDB access token (optional, for authenticated requests)
    
    Returns:
        Dictionary with movie info including poster_path, or None if not found
    """
    # Use default API key if not provided
    if not api_key:
        api_key = DEFAULT_API_KEY
    
    # Remove year from title if present (e.g., "Movie (1995)" -> "Movie")
    title_clean = re.sub(r'\s*\(\d{4}\)\s*$', '', movie_title).strip()
    
    # TMDB API endpoint (requires API key)
    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={title_clean}"
    
    try:
        headers = {
            'Accept': 'application/json',
        }
        # Use access token if provided (for authenticated requests)
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
            print(f"  Error: Invalid API key. Please check your TMDB API key.")
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
            print(f"    Error downloading image (Status: {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"    Error downloading image: {e}")
        return False


def get_movie_image_alternative(movie_title: str, save_path: str) -> bool:
    """
    Alternative method: Try to get image from a public movie database.
    This is a fallback if TMDB doesn't work.
    
    Args:
        movie_title: Movie title
        save_path: Path to save image
    
    Returns:
        True if successful, False otherwise
    """
    # This is a placeholder - in practice, you might use:
    # - OMDb API (requires API key)
    # - Web scraping (complex, not recommended)
    # - Local image database
    
    # For now, return False to indicate no alternative method
    return False


def download_movie_images(top_movies_df, output_dir: str = "movie_posters", 
                          api_key: str = None, access_token: str = None, use_alternative: bool = False):
    """
    Download poster images for top movies.
    
    Args:
        top_movies_df: DataFrame with top movies
        output_dir: Directory to save images
        api_key: TMDB API key (uses default if not provided)
        access_token: TMDB access token (optional)
        use_alternative: Whether to use alternative image sources if TMDB fails
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nSaving images to: {os.path.abspath(output_dir)}")
    print("="*80)
    
    downloaded = 0
    failed = 0
    
    for i, row in enumerate(top_movies_df.itertuples(), 1):
        movie_title = row.title
        movie_id = row.movieId
        
        print(f"\n[{i}/{len(top_movies_df)}] Processing: {movie_title}")
        
        # Search for movie on TMDB
        movie_info = search_movie_tmdb(movie_title, api_key, access_token)
        
        if movie_info and movie_info.get('poster_path'):
            # Create sanitized filename
            safe_filename = sanitize_filename(movie_title)
            file_extension = ".jpg"  # TMDB posters are typically JPG
            save_path = os.path.join(output_dir, f"{safe_filename}{file_extension}")
            
            # Download poster
            print(f"  Downloading poster...")
            if download_poster(movie_info['poster_path'], save_path):
                print(f"  [OK] Saved: {save_path}")
                downloaded += 1
            else:
                print(f"  [FAILED] Failed to download")
                failed += 1
        else:
            print(f"  [NOT FOUND] Poster not found on TMDB")
            if use_alternative:
                # Try alternative method
                safe_filename = sanitize_filename(movie_title)
                save_path = os.path.join(output_dir, f"{safe_filename}.jpg")
                if get_movie_image_alternative(movie_title, save_path):
                    print(f"  ✓ Saved using alternative method: {save_path}")
                    downloaded += 1
                else:
                    failed += 1
            else:
                failed += 1
    
    print("\n" + "="*80)
    print(f"Download complete!")
    print(f"  Successfully downloaded: {downloaded} images")
    print(f"  Failed: {failed} images")
    print(f"  Images saved in: {os.path.abspath(output_dir)}")
    print("="*80)


def main():
    """Main function to download movie images."""
    # Check for API key in environment variable, otherwise use default
    env_api_key = os.environ.get('TMDB_API_KEY', None)
    default_api_key = env_api_key if env_api_key else DEFAULT_API_KEY
    
    env_access_token = os.environ.get('TMDB_ACCESS_TOKEN', None)
    default_access_token = env_access_token if env_access_token else DEFAULT_ACCESS_TOKEN
    
    parser = argparse.ArgumentParser(
        description='Download movie poster images for top movies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_movie_images.py
  python download_movie_images.py --top-n 10 --output-dir posters
  python download_movie_images.py --top-n 20 --min-ratings 100 --api-key YOUR_API_KEY

Note: For best results, get a free API key from https://www.themoviedb.org/
        """
    )
    
    parser.add_argument(
        '--top-n',
        type=int,
        default=10,
        help='Number of top movies to download images for (default: 10)'
    )
    
    parser.add_argument(
        '--min-ratings',
        type=int,
        default=100,
        help='Minimum number of ratings required (default: 100)'
    )
    
    parser.add_argument(
        '--sort-by',
        type=str,
        choices=['average', 'count'],
        default='average',
        help='How to sort movies (default: average)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='movie_posters',
        help='Directory to save images (default: movie_posters)'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        default=default_api_key,
        help='TMDB API key (default: hardcoded key). Can override with --api-key or set TMDB_API_KEY environment variable.'
    )
    
    parser.add_argument(
        '--access-token',
        type=str,
        default=default_access_token,
        help='TMDB access token (optional, default: hardcoded token). Can override with --access-token or set TMDB_ACCESS_TOKEN environment variable.'
    )
    
    parser.add_argument(
        '--ratings',
        type=str,
        default='dataset/ratings.csv',
        help='Path to ratings.csv file'
    )
    
    parser.add_argument(
        '--movies',
        type=str,
        default='dataset/movies.csv',
        help='Path to movies.csv file'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.top_n <= 0:
        print("Error: --top-n must be a positive integer")
        sys.exit(1)
    
    if args.min_ratings < 1:
        print("Error: --min-ratings must be at least 1")
        sys.exit(1)
    
    # Use default API key if not provided
    if not args.api_key:
        args.api_key = DEFAULT_API_KEY
    if not args.access_token:
        args.access_token = DEFAULT_ACCESS_TOKEN
    
    try:
        # Load data
        ratings, movies = load_data(args.ratings, args.movies)
        
        # Get top movies
        top_movies = get_top_movies(
            ratings=ratings,
            movies=movies,
            top_n=args.top_n,
            min_ratings=args.min_ratings,
            sort_by=args.sort_by
        )
        
        if len(top_movies) == 0:
            print("No movies found matching the criteria.")
            sys.exit(1)
        
        # Download images
        download_movie_images(
            top_movies,
            output_dir=args.output_dir,
            api_key=args.api_key,
            access_token=args.access_token,
            use_alternative=False
        )
        
    except FileNotFoundError as e:
        print(f"Error: Could not find data file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

