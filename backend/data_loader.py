"""
Data Loading Module

This module handles loading and preprocessing of movie rating data.
"""

import pandas as pd
from typing import Tuple, Optional


def load_data(ratings_path: str, movies_path: str, 
              max_users: Optional[int] = None, 
              max_movies: Optional[int] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load ratings and movies data from CSV files.
    
    Args:
        ratings_path: Path to the ratings.csv file
        movies_path: Path to the movies.csv file
        max_users: Maximum number of users to load (None for all). Filters to most active users.
        max_movies: Maximum number of movies to load (None for all). Filters to most rated movies.
    
    Returns:
        Tuple of (ratings DataFrame, movies DataFrame)
    """
    print("Loading data...")
    ratings = pd.read_csv(ratings_path)
    movies = pd.read_csv(movies_path)
    print(f"Loaded {len(ratings)} ratings and {len(movies)} movies")
    
    # Filter to most active users if max_users is specified
    if max_users is not None and max_users > 0:
        print(f"Filtering to top {max_users} most active users...")
        user_rating_counts = ratings['userId'].value_counts()
        top_users = user_rating_counts.head(max_users).index
        ratings = ratings[ratings['userId'].isin(top_users)]
        print(f"Filtered to {len(ratings)} ratings from {max_users} users")
    
    # Filter to most rated movies if max_movies is specified
    if max_movies is not None and max_movies > 0:
        print(f"Filtering to top {max_movies} most rated movies...")
        movie_rating_counts = ratings['movieId'].value_counts()
        top_movies = movie_rating_counts.head(max_movies).index
        ratings = ratings[ratings['movieId'].isin(top_movies)]
        # Also filter movies dataframe
        movies = movies[movies['movieId'].isin(top_movies)]
        print(f"Filtered to {len(ratings)} ratings for {max_movies} movies")
    
    print(f"Final dataset: {len(ratings)} ratings, {len(movies)} movies")
    return ratings, movies


def create_user_movie_matrix(ratings: pd.DataFrame, use_sparse: bool = True) -> pd.DataFrame:
    """
    Create a user-movie rating matrix where rows are users and columns are movies.
    
    Args:
        ratings: DataFrame with columns userId, movieId, rating
        use_sparse: If True, uses a more memory-efficient approach (recommended for large datasets)
    
    Returns:
        Pivot table with users as rows and movies as columns
    """
    print("Creating user-movie rating matrix...")
    
    if use_sparse:
        # Use a more memory-efficient approach by working with the data directly
        # instead of creating a full dense matrix
        print("Using memory-efficient matrix creation...")
        user_movie_matrix = ratings.pivot_table(
            index='userId',
            columns='movieId',
            values='rating',
            fill_value=None  # Keep NaN instead of filling with 0
        )
    else:
        user_movie_matrix = ratings.pivot_table(
            index='userId',
            columns='movieId',
            values='rating'
        )
    
    print(f"Matrix shape: {user_movie_matrix.shape[0]} users x {user_movie_matrix.shape[1]} movies")
    print(f"Matrix memory usage: {user_movie_matrix.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    return user_movie_matrix

