"""
Simple User-Based Collaborative Filtering Recommender System

This module implements a basic recommender system that:
- Uses explicit ratings from users
- Measures user similarity using Pearson Correlation
- Recommends movies that the target user has not rated yet
- Outputs a Top-N recommendation list
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


def load_data(ratings_path: str, movies_path: str, 
              max_users: int = None, max_movies: int = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
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
    
    # Calculate Pearson correlation
    correlation = ratings1.corr(ratings2, method='pearson')
    
    # Return 0 if correlation is NaN (happens when variance is 0)
    return correlation if not np.isnan(correlation) else 0.0


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


def generate_recommendations(target_user_id: int, user_movie_matrix: pd.DataFrame,
                            movies: pd.DataFrame, top_n: int = 10,
                            min_common_movies: int = 5, top_k_similar: int = 50) -> List[Tuple[int, str, float]]:
    """
    Generate Top-N movie recommendations for a target user.
    
    Args:
        target_user_id: ID of the user to generate recommendations for
        user_movie_matrix: User-movie rating matrix
        movies: DataFrame with movie information (movieId, title, genres)
        top_n: Number of recommendations to return
        min_common_movies: Minimum common movies for similarity calculation
        top_k_similar: Number of similar users to consider for predictions
    
    Returns:
        List of tuples (movie_id, movie_title, predicted_rating) sorted by predicted rating
    """
    print(f"\nGenerating recommendations for user {target_user_id}...")
    
    # Check if user exists
    if target_user_id not in user_movie_matrix.index:
        print(f"Error: User {target_user_id} not found in the dataset")
        print(f"Available users: {len(user_movie_matrix.index)} users (IDs: {sorted(user_movie_matrix.index)[:10]} ...)")
        print("Tip: Use --max-users to include more users, or try a different user ID")
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
            # Get movie title
            movie_info = movies[movies['movieId'] == movie_id]
            if len(movie_info) > 0:
                movie_title = movie_info.iloc[0]['title']
                predictions.append((movie_id, movie_title, predicted_rating))
    
    # Sort by predicted rating (highest first) and return top N
    predictions.sort(key=lambda x: x[2], reverse=True)
    recommendations = predictions[:top_n]
    
    print(f"Generated {len(recommendations)} recommendations")
    return recommendations


def display_recommendations(recommendations: List[Tuple[int, str, float]], 
                           download_images: bool = False,
                           image_dir: str = "movie_posters"):
    """
    Display recommendations in a user-friendly format.
    
    Args:
        recommendations: List of (movie_id, movie_title, predicted_rating) tuples
        download_images: Whether to download missing poster images automatically
        image_dir: Directory where movie poster images are stored
    """
    if len(recommendations) == 0:
        print("\nNo recommendations available.")
        return
    
    # Download images if requested
    if download_images:
        try:
            from image_downloader import ensure_movie_images
            recommendations_with_images = ensure_movie_images(
                recommendations,
                output_dir=image_dir,
                verbose=True
            )
            # Update recommendations to include image paths
            recommendations = [(mid, title, rating) for mid, title, rating, _ in recommendations_with_images]
        except ImportError:
            print("Warning: image_downloader module not found. Skipping image download.")
        except Exception as e:
            print(f"Warning: Could not download images: {e}")
    
    print("\n" + "="*70)
    print("TOP RECOMMENDATIONS")
    print("="*70)
    
    for i, (movie_id, title, predicted_rating) in enumerate(recommendations, 1):
        print(f"{i:2d}. {title}")
        print(f"    Movie ID: {movie_id} | Predicted Rating: {predicted_rating:.2f}/5.0")
        print()
    
    print("="*70)


def get_top_movies(ratings: pd.DataFrame, movies: pd.DataFrame, 
                   top_n: int = 20, min_ratings: int = 10,
                   sort_by: str = 'average') -> pd.DataFrame:
    """
    Get the top movies based on ratings from all users.
    
    Args:
        ratings: DataFrame with columns userId, movieId, rating
        movies: DataFrame with movie information (movieId, title, genres)
        top_n: Number of top movies to return
        min_ratings: Minimum number of ratings required for a movie to be considered
        sort_by: How to sort movies ('average' for average rating, 'count' for number of ratings)
    
    Returns:
        DataFrame with top movies including title, average rating, and number of ratings
    """
    print(f"\nCalculating top movies from all users...")
    
    # Calculate statistics for each movie
    movie_stats = ratings.groupby('movieId').agg({
        'rating': ['mean', 'count']
    }).reset_index()
    
    # Flatten column names
    movie_stats.columns = ['movieId', 'average_rating', 'num_ratings']
    
    # Filter movies with minimum number of ratings
    movie_stats = movie_stats[movie_stats['num_ratings'] >= min_ratings]
    
    # Merge with movie information
    movie_stats = movie_stats.merge(movies[['movieId', 'title', 'genres']], on='movieId', how='left')
    
    # Sort based on criteria
    if sort_by == 'average':
        # Sort by average rating (descending), then by number of ratings (descending) as tiebreaker
        movie_stats = movie_stats.sort_values(
            ['average_rating', 'num_ratings'], 
            ascending=[False, False]
        )
    elif sort_by == 'count':
        # Sort by number of ratings (descending), then by average rating (descending) as tiebreaker
        movie_stats = movie_stats.sort_values(
            ['num_ratings', 'average_rating'], 
            ascending=[False, False]
        )
    else:
        # Default: sort by average rating
        movie_stats = movie_stats.sort_values('average_rating', ascending=False)
    
    # Get top N
    top_movies = movie_stats.head(top_n)
    
    print(f"Found {len(top_movies)} top movies (minimum {min_ratings} ratings required)")
    return top_movies


def display_top_movies(top_movies: pd.DataFrame, sort_by: str = 'average'):
    """
    Display top movies in a user-friendly format.
    
    Args:
        top_movies: DataFrame with top movies
        sort_by: How movies are sorted ('average' or 'count')
    """
    if len(top_movies) == 0:
        print("\nNo movies found.")
        return
    
    print("\n" + "="*80)
    if sort_by == 'average':
        print("TOP MOVIES BY AVERAGE RATING (All Users)")
    else:
        print("TOP MOVIES BY POPULARITY (Number of Ratings)")
    print("="*80)
    
    for i, row in enumerate(top_movies.itertuples(), 1):
        print(f"{i:2d}. {row.title}")
        print(f"    Average Rating: {row.average_rating:.2f}/5.0 | "
              f"Number of Ratings: {int(row.num_ratings):,} | "
              f"Genres: {row.genres}")
        print()
    
    print("="*80)


def get_top_movies_by_genre(ratings: pd.DataFrame, movies: pd.DataFrame,
                            genre: str, top_n: int = 20, min_ratings: int = 10,
                            sort_by: str = 'average') -> pd.DataFrame:
    """
    Get the top movies for a specific genre.
    
    Args:
        ratings: DataFrame with columns userId, movieId, rating
        movies: DataFrame with movie information (movieId, title, genres)
        genre: Genre to filter by (e.g., "Action", "Comedy", "Drama")
        top_n: Number of top movies to return
        min_ratings: Minimum number of ratings required for a movie to be considered
        sort_by: How to sort movies ('average' for average rating, 'count' for number of ratings)
    
    Returns:
        DataFrame with top movies in the specified genre
    """
    print(f"\nCalculating top {genre} movies from all users...")
    
    # Filter movies by genre (case-insensitive)
    # Genres are pipe-separated, so we check if the genre string is in the genres column
    genre_filter = movies['genres'].str.contains(genre, case=False, na=False)
    genre_movies = movies[genre_filter].copy()
    
    if len(genre_movies) == 0:
        print(f"No movies found with genre '{genre}'")
        return pd.DataFrame()
    
    print(f"Found {len(genre_movies)} movies with genre '{genre}'")
    
    # Get movie IDs for this genre
    genre_movie_ids = set(genre_movies['movieId'].unique())
    
    # Filter ratings to only include movies in this genre
    genre_ratings = ratings[ratings['movieId'].isin(genre_movie_ids)]
    
    # Calculate statistics for each movie
    movie_stats = genre_ratings.groupby('movieId').agg({
        'rating': ['mean', 'count']
    }).reset_index()
    
    # Flatten column names
    movie_stats.columns = ['movieId', 'average_rating', 'num_ratings']
    
    # Filter movies with minimum number of ratings
    movie_stats = movie_stats[movie_stats['num_ratings'] >= min_ratings]
    
    # Merge with movie information
    movie_stats = movie_stats.merge(genre_movies[['movieId', 'title', 'genres']], on='movieId', how='left')
    
    # Sort based on criteria
    if sort_by == 'average':
        # Sort by average rating (descending), then by number of ratings (descending) as tiebreaker
        movie_stats = movie_stats.sort_values(
            ['average_rating', 'num_ratings'], 
            ascending=[False, False]
        )
    elif sort_by == 'count':
        # Sort by number of ratings (descending), then by average rating (descending) as tiebreaker
        movie_stats = movie_stats.sort_values(
            ['num_ratings', 'average_rating'], 
            ascending=[False, False]
        )
    else:
        # Default: sort by average rating
        movie_stats = movie_stats.sort_values('average_rating', ascending=False)
    
    # Get top N
    top_movies = movie_stats.head(top_n)
    
    print(f"Found {len(top_movies)} top {genre} movies (minimum {min_ratings} ratings required)")
    return top_movies


def display_top_movies_by_genre(top_movies: pd.DataFrame, genre: str, sort_by: str = 'average'):
    """
    Display top movies by genre in a user-friendly format.
    
    Args:
        top_movies: DataFrame with top movies
        genre: Genre name
        sort_by: How movies are sorted ('average' or 'count')
    """
    if len(top_movies) == 0:
        print(f"\nNo {genre} movies found matching the criteria.")
        return
    
    print("\n" + "="*80)
    if sort_by == 'average':
        print(f"TOP {genre.upper()} MOVIES BY AVERAGE RATING (All Users)")
    else:
        print(f"TOP {genre.upper()} MOVIES BY POPULARITY (Number of Ratings)")
    print("="*80)
    
    for i, row in enumerate(top_movies.itertuples(), 1):
        print(f"{i:2d}. {row.title}")
        print(f"    Average Rating: {row.average_rating:.2f}/5.0 | "
              f"Number of Ratings: {int(row.num_ratings):,} | "
              f"Genres: {row.genres}")
        print()
    
    print("="*80)


def list_available_genres(movies: pd.DataFrame) -> List[str]:
    """
    Get a list of all available genres in the dataset.
    
    Args:
        movies: DataFrame with movie information
    
    Returns:
        Sorted list of unique genres
    """
    # Split pipe-separated genres and get unique values
    all_genres = set()
    for genres_str in movies['genres'].dropna():
        if genres_str and genres_str != '(no genres listed)':
            genres = [g.strip() for g in genres_str.split('|')]
            all_genres.update(genres)
    
    return sorted(list(all_genres))

