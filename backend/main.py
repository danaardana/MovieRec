"""
Main Backend Entry Point for MovieRec

This module provides the main API endpoint for the recommendation system.
It can be used as a standalone script or integrated with a web framework.
"""

import sys
import os
from typing import List, Tuple, Optional, Dict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.data_loader import load_data, create_user_movie_matrix
from backend.recommender import generate_recommendations
from backend.utils import ensure_movie_images, get_movie_overview


def get_recommendations(user_id: int,
                       top_n: int = 4,
                       genre: Optional[str] = None,
                       ratings_path: str = 'dataset/ratings.csv',
                       movies_path: str = 'dataset/movies.csv',
                       max_users: int = 2000,
                       max_movies: int = 2000,
                       download_images: bool = True,
                       image_dir: str = 'movie_posters') -> Tuple[List[Dict], bool]:
    """
    Get movie recommendations for a user.
    
    This is the main function that should be called by the frontend.
    
    Args:
        user_id: ID of the user to generate recommendations for
        top_n: Number of recommendations to return (default: 4)
        genre: Optional genre filter (applied after recommendation)
        ratings_path: Path to ratings.csv file
        movies_path: Path to movies.csv file
        max_users: Maximum number of users to load (for memory efficiency)
        max_movies: Maximum number of movies to load (for memory efficiency)
        download_images: Whether to download poster images automatically
        image_dir: Directory where images are stored
    
    Returns:
        Tuple of (recommendations, is_cold_start):
        - recommendations: List of dictionaries, each containing:
          {
              'movie_id': int,
              'title': str,
              'predicted_rating': float,
              'genres': str,
              'image_path': str or None,
              'overview': str or None,
              'release_year': str or None,
              'similar_user_ids': List[int]
          }
        - is_cold_start: Boolean indicating if popular movies fallback was used
    """
    # Load data (include requested user even if not in top N)
    ratings, movies = load_data(ratings_path, movies_path, max_users=max_users, max_movies=max_movies, required_user_id=user_id)
    
    # Create user-movie matrix
    user_movie_matrix = create_user_movie_matrix(ratings, use_sparse=True)
    
    # Generate recommendations
    recommendations, is_cold_start = generate_recommendations(
        target_user_id=user_id,
        user_movie_matrix=user_movie_matrix,
        movies=movies,
        top_n=top_n,
        genre_filter=genre,
        min_common_movies=5,
        top_k_similar=50
    )
    
    if not recommendations:
        return [], False
    
    # Download images if requested
    image_paths = {}
    if download_images:
        try:
            # ensure_movie_images expects (movie_id, title, predicted_rating) tuples
            # recommendations now has 5 elements: (movie_id, title, predicted_rating, genres, similar_user_ids)
            recommendations_for_images = [(mid, title, rating) for mid, title, rating, _, _ in recommendations]
            recommendations_with_images = ensure_movie_images(
                recommendations_for_images,
                output_dir=image_dir,
                verbose=False
            )
            # Map titles to image paths
            # ensure_movie_images returns (movie_id, title, predicted_rating, image_path)
            image_paths = {title: path for _, title, _, path in recommendations_with_images}
        except Exception as e:
            print(f"Warning: Could not download images: {e}")
    
    # Format results for frontend
    results = []
    for rec in recommendations:
        # Handle both old format (4 items) and new format (5 items with similar_user_ids)
        if len(rec) == 5:
            movie_id, title, predicted_rating, genres, similar_user_ids = rec
        else:
            movie_id, title, predicted_rating, genres = rec
            similar_user_ids = []
        # Extract release year from title (format: "Title (YYYY)")
        import re
        year_match = re.search(r'\((\d{4})\)', title)
        release_year = year_match.group(1) if year_match else None
        
        # Get overview from API
        overview = None
        try:
            overview = get_movie_overview(title)
        except Exception:
            pass
        
        result = {
            'movie_id': int(movie_id),
            'title': title,
            'predicted_rating': round(predicted_rating, 2),
            'genres': genres,
            'image_path': image_paths.get(title),
            'overview': overview,
            'release_year': release_year,
            'similar_user_ids': similar_user_ids[:10]  # Limit to top 10
        }
        results.append(result)
    
    return results, is_cold_start


if __name__ == '__main__':
    # Example usage for testing
    import argparse
    
    parser = argparse.ArgumentParser(description='MovieRec Backend API')
    parser.add_argument('--user', type=int, required=True, help='User ID')
    parser.add_argument('--top-n', type=int, default=4, help='Number of recommendations')
    parser.add_argument('--genre', type=str, default=None, help='Genre filter')
    
    args = parser.parse_args()
    
    recommendations, is_cold_start = get_recommendations(
        user_id=args.user,
        top_n=args.top_n,
        genre=args.genre
    )
    
    if is_cold_start:
        print("\n⚠️  Cold Start: Using popular movies fallback (no similar users found)")
    
    print(f"\nFound {len(recommendations)} recommendations:")
    for rec in recommendations:
        print(f"  - {rec['title']} (Rating: {rec['predicted_rating']}/5.0)")

