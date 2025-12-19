"""
Collaborative Filtering Module

This module implements User-Based Collaborative Filtering for movie recommendations.
"""

import pandas as pd
from typing import List, Tuple, Optional
from .similarity import find_similar_users
from .prediction import predict_rating, get_similar_users_who_rated


def get_popular_movies_fallback(user_movie_matrix: pd.DataFrame,
                                movies: pd.DataFrame,
                                target_user_id: int,
                                top_n: int = 10,
                                genre_filter: Optional[str] = None,
                                min_ratings: int = 10) -> List[Tuple[int, str, float, str, List[int]]]:
    """
    Fallback recommendation method using popular movies when CF fails (cold start problem).
    
    Returns top movies by average rating, excluding movies the user has already rated.
    This is used when no similar users are found for collaborative filtering.
    
    Args:
        user_movie_matrix: User-movie rating matrix
        movies: DataFrame with movie information (movieId, title, genres)
        target_user_id: ID of the user (to exclude their rated movies)
        top_n: Number of recommendations to return
        genre_filter: Optional genre to filter recommendations
        min_ratings: Minimum number of ratings required for a movie to be considered
    
    Returns:
        List of tuples (movie_id, movie_title, average_rating, genres, []) 
        sorted by average rating, where the last element is empty list (no similar users)
    """
    print(f"Warning: No similar users found for user {target_user_id}")
    print(f"Using popular movies fallback (cold start solution)...")
    
    # Get movies the user has already rated (to exclude them)
    if target_user_id in user_movie_matrix.index:
        user_ratings = user_movie_matrix.loc[target_user_id]
        rated_movies = set(user_ratings.dropna().index)
    else:
        rated_movies = set()
    
    # Calculate average rating and count for each movie
    movie_stats = []
    for movie_id in user_movie_matrix.columns:
        # Get all ratings for this movie (excluding NaN)
        movie_ratings = user_movie_matrix[movie_id].dropna()
        
        # Skip if not enough ratings
        if len(movie_ratings) < min_ratings:
            continue
        
        # Skip if user already rated this movie
        if movie_id in rated_movies:
            continue
        
        # Calculate average rating
        avg_rating = movie_ratings.mean()
        
        # Get movie info
        movie_info = movies[movies['movieId'] == movie_id]
        if len(movie_info) > 0:
            movie_title = movie_info.iloc[0]['title']
            movie_genres = movie_info.iloc[0]['genres']
            
            # Apply genre filter if specified
            if genre_filter:
                if genre_filter.lower() not in movie_genres.lower():
                    continue
            
            movie_stats.append({
                'movie_id': movie_id,
                'title': movie_title,
                'avg_rating': avg_rating,
                'num_ratings': len(movie_ratings),
                'genres': movie_genres
            })
    
    # Sort by average rating (descending), then by number of ratings (descending) as tiebreaker
    movie_stats.sort(key=lambda x: (x['avg_rating'], x['num_ratings']), reverse=True)
    
    # Get top N and format as tuples
    recommendations = []
    for movie in movie_stats[:top_n]:
        recommendations.append((
            movie['movie_id'],
            movie['title'],
            movie['avg_rating'],
            movie['genres'],
            []  # Empty list for similar_user_ids (not applicable for popular movies)
        ))
    
    print(f"Generated {len(recommendations)} popular movie recommendations")
    if genre_filter:
        print(f"Filtered by genre: {genre_filter}")
    
    return recommendations


def generate_recommendations(target_user_id: int, 
                            user_movie_matrix: pd.DataFrame,
                            movies: pd.DataFrame, 
                            top_n: int = 10,
                            min_common_movies: int = 5, 
                            top_k_similar: int = 50,
                            genre_filter: Optional[str] = None) -> Tuple[List[Tuple[int, str, float, str, List[int]]], bool]:
    """
    Generate Top-N movie recommendations for a target user using User-Based Collaborative Filtering.
    
    The genre filter is applied AFTER recommendation generation, not during similarity computation.
    This ensures recommendations are based purely on user preferences, then filtered by genre.
    
    Args:
        target_user_id: ID of the user to generate recommendations for
        user_movie_matrix: User-movie rating matrix
        movies: DataFrame with movie information (movieId, title, genres)
        top_n: Number of recommendations to return
        min_common_movies: Minimum common movies for similarity calculation
        top_k_similar: Number of similar users to consider for predictions
        genre_filter: Optional genre to filter recommendations (applied after prediction)
    
    Returns:
        Tuple of (recommendations, is_cold_start):
        - recommendations: List of tuples (movie_id, movie_title, predicted_rating, genres, similar_user_ids) 
          sorted by predicted rating, where similar_user_ids is a list of user IDs who rated the movie
        - is_cold_start: Boolean indicating if popular movies fallback was used (True) or CF was used (False)
    """
    print(f"\nGenerating recommendations for user {target_user_id}...")
    
    # Check if user exists
    if target_user_id not in user_movie_matrix.index:
        print(f"Error: User {target_user_id} not found in the dataset")
        print(f"Available users: {len(user_movie_matrix.index)} users (IDs: {sorted(user_movie_matrix.index)[:10]} ...)")
        return [], False
    
    # Get movies the user has already rated
    user_ratings = user_movie_matrix.loc[target_user_id]
    rated_movies = set(user_ratings.dropna().index)
    
    # Find similar users
    similar_users = find_similar_users(target_user_id, user_movie_matrix, min_common_movies)
    
    if len(similar_users) == 0:
        print(f"Warning: No similar users found for user {target_user_id}")
        print(f"Using popular movies fallback (cold start solution)...")
        # Use popular movies as fallback
        return get_popular_movies_fallback(
            user_movie_matrix=user_movie_matrix,
            movies=movies,
            target_user_id=target_user_id,
            top_n=top_n,
            genre_filter=genre_filter,
            min_ratings=10
        ), True  # Return True to indicate cold start
    
    # Predict ratings for movies the user hasn't rated
    predictions = []
    all_movies = set(user_movie_matrix.columns)
    unrated_movies = all_movies - rated_movies
    
    print(f"Predicting ratings for {len(unrated_movies)} unrated movies...")
    
    for movie_id in unrated_movies:
        predicted_rating = predict_rating(
            target_user_id, movie_id, user_movie_matrix,
            similar_users, top_k_similar
        )
        
        if predicted_rating > 0:
            # Get movie information
            movie_info = movies[movies['movieId'] == movie_id]
            if len(movie_info) > 0:
                movie_title = movie_info.iloc[0]['title']
                movie_genres = movie_info.iloc[0]['genres']
                
                # Apply genre filter if specified (AFTER prediction)
                if genre_filter:
                    if genre_filter.lower() not in movie_genres.lower():
                        continue
                
                # Get similar users who rated this movie
                similar_user_ids = get_similar_users_who_rated(
                    movie_id, user_movie_matrix, similar_users, top_k=10
                )
                
                predictions.append((movie_id, movie_title, predicted_rating, movie_genres, similar_user_ids))
    
    # Sort by predicted rating (highest first) and return top N
    predictions.sort(key=lambda x: x[2], reverse=True)
    recommendations = predictions[:top_n]
    
    # If no recommendations found (e.g., due to genre filter or low predictions), use fallback
    if len(recommendations) == 0:
        print(f"Warning: No CF recommendations generated (possibly due to genre filter or low predictions)")
        print(f"Using popular movies fallback...")
        return get_popular_movies_fallback(
            user_movie_matrix=user_movie_matrix,
            movies=movies,
            target_user_id=target_user_id,
            top_n=top_n,
            genre_filter=genre_filter,
            min_ratings=10
        ), True  # Return True to indicate cold start
    
    print(f"Generated {len(recommendations)} recommendations")
    if genre_filter:
        print(f"Filtered by genre: {genre_filter}")
    
    return recommendations, False  # Return False to indicate normal CF was used

