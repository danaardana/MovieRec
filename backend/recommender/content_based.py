"""
Content-Based Filtering Module

This module implements content-based filtering using movie genres and user preferences.
It recommends movies similar to those the user has liked in the past based on genre similarity.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Set
from collections import Counter


def parse_genres(genres_str: str) -> Set[str]:
    """
    Parse genres string into a set of genre names.
    
    Args:
        genres_str: Genre string in format "Action|Adventure|Sci-Fi"
    
    Returns:
        Set of genre names
    """
    if pd.isna(genres_str) or not genres_str:
        return set()
    return set(genre.strip() for genre in str(genres_str).split('|') if genre.strip())


def build_user_genre_profile(user_ratings: pd.Series, movies: pd.DataFrame, 
                             min_rating: float = 3.5) -> Dict[str, float]:
    """
    Build a genre preference profile for a user based on their high ratings.
    
    Args:
        user_ratings: Series of ratings for movies (indexed by movieId)
        movies: DataFrame with movie information including genres
        min_rating: Minimum rating to consider a movie as "liked"
    
    Returns:
        Dictionary mapping genre to preference score (weighted by rating)
    """
    genre_scores = Counter()
    total_weight = 0.0
    
    # Consider movies the user rated highly
    liked_movies = user_ratings[user_ratings >= min_rating]
    
    for movie_id, rating in liked_movies.items():
        # Get genres for this movie
        movie_info = movies[movies['movieId'] == movie_id]
        if len(movie_info) > 0:
            genres = parse_genres(movie_info.iloc[0]['genres'])
            
            # Weight by rating (higher rating = stronger preference)
            weight = rating - min_rating + 1  # Normalize so min_rating has weight 1
            
            for genre in genres:
                genre_scores[genre] += weight
                total_weight += weight
    
    # Normalize scores to get preference percentages
    if total_weight > 0:
        genre_profile = {genre: score / total_weight for genre, score in genre_scores.items()}
    else:
        genre_profile = {}
    
    return genre_profile


def calculate_content_similarity(movie_genres: Set[str], 
                                 user_profile: Dict[str, float]) -> float:
    """
    Calculate similarity between a movie and user's genre profile.
    
    Uses cosine similarity between movie genre vector and user profile vector.
    
    Args:
        movie_genres: Set of genres for the movie
        user_profile: User's genre preference profile (genre -> score)
    
    Returns:
        Similarity score between 0 and 1
    """
    if not movie_genres or not user_profile:
        return 0.0
    
    # Get all unique genres
    all_genres = set(movie_genres) | set(user_profile.keys())
    
    # Build vectors
    movie_vector = np.array([1.0 if genre in movie_genres else 0.0 for genre in all_genres])
    user_vector = np.array([user_profile.get(genre, 0.0) for genre in all_genres])
    
    # Calculate cosine similarity
    dot_product = np.dot(movie_vector, user_vector)
    movie_norm = np.linalg.norm(movie_vector)
    user_norm = np.linalg.norm(user_vector)
    
    if movie_norm == 0 or user_norm == 0:
        return 0.0
    
    similarity = dot_product / (movie_norm * user_norm)
    return float(similarity)


def content_based_recommendations(target_user_id: int,
                                 user_movie_matrix: pd.DataFrame,
                                 movies: pd.DataFrame,
                                 top_n: int = 10,
                                 min_rating: float = 3.5,
                                 genre_filter: str = None) -> List[Tuple[int, str, float, str]]:
    """
    Generate content-based recommendations for a user.
    
    Recommends movies similar to those the user has liked based on genre similarity.
    
    Args:
        target_user_id: ID of the target user
        user_movie_matrix: User-movie rating matrix
        movies: DataFrame with movie information (movieId, title, genres)
        top_n: Number of recommendations to return
        min_rating: Minimum rating to consider a movie as "liked"
        genre_filter: Optional genre filter (applied after recommendation)
    
    Returns:
        List of tuples (movie_id, title, similarity_score, genres)
        sorted by similarity score
    """
    if target_user_id not in user_movie_matrix.index:
        return []
    
    # Get user's ratings
    user_ratings = user_movie_matrix.loc[target_user_id]
    rated_movies = set(user_ratings.dropna().index)
    
    # Build user's genre profile
    user_profile = build_user_genre_profile(user_ratings, movies, min_rating)
    
    if not user_profile:
        # User has no highly-rated movies, can't build profile
        return []
    
    # Calculate similarity for unrated movies
    recommendations = []
    all_movies = set(user_movie_matrix.columns)
    unrated_movies = all_movies - rated_movies
    
    for movie_id in unrated_movies:
        # Get movie genres
        movie_info = movies[movies['movieId'] == movie_id]
        if len(movie_info) > 0:
            genres_str = movie_info.iloc[0]['genres']
            movie_genres = parse_genres(genres_str)
            movie_title = movie_info.iloc[0]['title']
            
            # Apply genre filter if specified
            if genre_filter:
                if genre_filter.lower() not in genres_str.lower():
                    continue
            
            # Calculate similarity
            similarity = calculate_content_similarity(movie_genres, user_profile)
            
            if similarity > 0:
                recommendations.append((
                    movie_id,
                    movie_title,
                    similarity,
                    genres_str
                ))
    
    # Sort by similarity (highest first) and return top N
    recommendations.sort(key=lambda x: x[2], reverse=True)
    return recommendations[:top_n]
