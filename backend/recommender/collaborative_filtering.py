"""
Collaborative Filtering Module

This module implements User-Based Collaborative Filtering for movie recommendations.
"""

import pandas as pd
from typing import List, Tuple, Optional
from .similarity import find_similar_users
from .prediction import predict_rating, get_similar_users_who_rated


def generate_recommendations(target_user_id: int, 
                            user_movie_matrix: pd.DataFrame,
                            movies: pd.DataFrame, 
                            top_n: int = 10,
                            min_common_movies: int = 5, 
                            top_k_similar: int = 50,
                            genre_filter: Optional[str] = None) -> List[Tuple[int, str, float, str]]:
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
        List of tuples (movie_id, movie_title, predicted_rating, genres, similar_user_ids) 
        sorted by predicted rating, where similar_user_ids is a list of user IDs who rated the movie
    """
    print(f"\nGenerating recommendations for user {target_user_id}...")
    
    # Check if user exists
    if target_user_id not in user_movie_matrix.index:
        print(f"Error: User {target_user_id} not found in the dataset")
        print(f"Available users: {len(user_movie_matrix.index)} users (IDs: {sorted(user_movie_matrix.index)[:10]} ...)")
        return []
    
    # Get movies the user has already rated
    user_ratings = user_movie_matrix.loc[target_user_id]
    rated_movies = set(user_ratings.dropna().index)
    
    # Find similar users
    similar_users = find_similar_users(target_user_id, user_movie_matrix, min_common_movies)
    
    if len(similar_users) == 0:
        print(f"Error: No similar users found for user {target_user_id}")
        return []
    
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
    
    print(f"Generated {len(recommendations)} recommendations")
    if genre_filter:
        print(f"Filtered by genre: {genre_filter}")
    
    return recommendations

