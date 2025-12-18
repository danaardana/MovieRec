"""
Similarity Computation Module

This module implements user similarity calculation using Pearson Correlation.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple


def pearson_correlation(user1_ratings: pd.Series, user2_ratings: pd.Series) -> float:
    """
    Calculate Pearson Correlation Coefficient between two users.
    
    Only considers movies that both users have rated.
    
    Args:
        user1_ratings: Ratings series for user 1
        user2_ratings: Ratings series for user 2
    
    Returns:
        Pearson correlation coefficient (between -1 and 1), or 0 if insufficient common ratings
    """
    # Find movies rated by both users
    common_movies = user1_ratings.dropna().index.intersection(user2_ratings.dropna().index)
    
    if len(common_movies) < 2:
        # Need at least 2 common movies for correlation
        return 0.0
    
    # Get ratings for common movies
    ratings1 = user1_ratings[common_movies]
    ratings2 = user2_ratings[common_movies]
    
    # Calculate means
    mean1 = ratings1.mean()
    mean2 = ratings2.mean()
    
    # Calculate numerator and denominators
    numerator = ((ratings1 - mean1) * (ratings2 - mean2)).sum()
    denom1 = ((ratings1 - mean1) ** 2).sum()
    denom2 = ((ratings2 - mean2) ** 2).sum()
    
    # Handle division by zero (when variance is 0)
    if denom1 == 0 or denom2 == 0:
        return 0.0
    
    # Calculate correlation
    correlation = numerator / np.sqrt(denom1 * denom2)
    
    # Return 0 if correlation is NaN or invalid
    if np.isnan(correlation) or np.isinf(correlation):
        return 0.0
    
    return float(correlation)


def find_similar_users(target_user_id: int, user_movie_matrix: pd.DataFrame, 
                       min_common_movies: int = 5) -> List[Tuple[int, float]]:
    """
    Find users similar to the target user using Pearson Correlation.
    
    Args:
        target_user_id: ID of the user to find similar users for
        user_movie_matrix: User-movie rating matrix
        min_common_movies: Minimum number of common movies required for similarity calculation
    
    Returns:
        List of tuples (user_id, similarity_score) sorted by similarity (highest first)
    """
    if target_user_id not in user_movie_matrix.index:
        return []
    
    print(f"Finding similar users for user {target_user_id}...")
    target_user_ratings = user_movie_matrix.loc[target_user_id]
    similarities = []
    
    for user_id in user_movie_matrix.index:
        if user_id == target_user_id:
            continue
        
        other_user_ratings = user_movie_matrix.loc[user_id]
        
        # Check if they have enough common movies
        common_movies = target_user_ratings.dropna().index.intersection(
            other_user_ratings.dropna().index
        )
        
        if len(common_movies) >= min_common_movies:
            similarity = pearson_correlation(target_user_ratings, other_user_ratings)
            if similarity > 0:  # Only consider positive correlations
                similarities.append((user_id, similarity))
    
    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x[1], reverse=True)
    print(f"Found {len(similarities)} similar users")
    return similarities

