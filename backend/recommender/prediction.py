"""
Rating Prediction Module

This module implements rating prediction using weighted averages from similar users.
"""

import pandas as pd
from typing import List, Tuple


def predict_rating(target_user_id: int, movie_id: int, user_movie_matrix: pd.DataFrame,
                   similar_users: List[Tuple[int, float]], top_k: int = 50) -> float:
    """
    Predict the rating a target user would give to a movie.
    
    Uses weighted average of similar users' ratings, weighted by similarity score.
    
    Args:
        target_user_id: ID of the target user
        movie_id: ID of the movie to predict rating for
        user_movie_matrix: User-movie rating matrix
        similar_users: List of (user_id, similarity_score) tuples
        top_k: Number of most similar users to consider
    
    Returns:
        Predicted rating (0 if cannot be predicted)
    """
    if movie_id not in user_movie_matrix.columns:
        return 0.0
    
    numerator = 0.0
    denominator = 0.0
    
    # Use top K similar users
    for user_id, similarity in similar_users[:top_k]:
        if movie_id in user_movie_matrix.columns:
            rating = user_movie_matrix.loc[user_id, movie_id]
            if not pd.isna(rating):
                numerator += similarity * rating
                denominator += abs(similarity)
    
    if denominator == 0:
        return 0.0
    
    predicted_rating = numerator / denominator
    return predicted_rating


def get_similar_users_who_rated(movie_id: int, user_movie_matrix: pd.DataFrame,
                                similar_users: List[Tuple[int, float]], top_k: int = 10) -> List[int]:
    """
    Get list of similar user IDs who rated a specific movie.
    
    Args:
        movie_id: ID of the movie
        user_movie_matrix: User-movie rating matrix
        similar_users: List of (user_id, similarity_score) tuples
        top_k: Maximum number of users to return
    
    Returns:
        List of user IDs who rated the movie, sorted by similarity (highest first)
    """
    if movie_id not in user_movie_matrix.columns:
        return []
    
    users_who_rated = []
    for user_id, similarity in similar_users[:top_k * 2]:  # Check more to get top_k
        if movie_id in user_movie_matrix.columns:
            rating = user_movie_matrix.loc[user_id, movie_id]
            if not pd.isna(rating):
                users_who_rated.append(user_id)
                if len(users_who_rated) >= top_k:
                    break
    
    return users_who_rated

