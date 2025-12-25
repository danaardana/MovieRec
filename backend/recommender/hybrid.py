"""
Hybrid Recommendation Module

This module combines User-Based Collaborative Filtering and Content-Based Filtering
to provide hybrid recommendations that leverage both approaches.
"""

import pandas as pd
from typing import List, Tuple, Optional
from collections import defaultdict

from .collaborative_filtering import generate_recommendations as cf_recommendations
from .content_based import content_based_recommendations


def hybrid_recommendations(target_user_id: int,
                          user_movie_matrix: pd.DataFrame,
                          movies: pd.DataFrame,
                          top_n: int = 10,
                          cf_weight: float = 0.7,
                          cb_weight: float = 0.3,
                          min_common_movies: int = 5,
                          top_k_similar: int = 50,
                          genre_filter: Optional[str] = None,
                          hybrid_method: str = 'weighted') -> Tuple[List[Tuple[int, str, float, str, List[int]]], bool]:
    """
    Generate hybrid recommendations combining Collaborative Filtering and Content-Based Filtering.
    
    Args:
        target_user_id: ID of the target user
        user_movie_matrix: User-movie rating matrix
        movies: DataFrame with movie information (movieId, title, genres)
        top_n: Number of recommendations to return
        cf_weight: Weight for collaborative filtering scores (0.0 to 1.0)
        cb_weight: Weight for content-based scores (0.0 to 1.0)
        min_common_movies: Minimum common movies for CF similarity calculation
        top_k_similar: Number of similar users to consider for CF
        genre_filter: Optional genre filter (applied after combination)
        hybrid_method: Combination method ('weighted', 'mixed', 'switching')
            - 'weighted': Weighted combination of scores
            - 'mixed': Take top recommendations from both approaches
            - 'switching': Use CF if available, fallback to CB
    
    Returns:
        Tuple of (recommendations, is_cold_start):
        - recommendations: List of tuples (movie_id, title, combined_score, genres, similar_user_ids)
        - is_cold_start: Boolean indicating if fallback was used
    """
    # Normalize weights
    total_weight = cf_weight + cb_weight
    if total_weight > 0:
        cf_weight = cf_weight / total_weight
        cb_weight = cb_weight / total_weight
    
    if hybrid_method == 'switching':
        # Try CF first, fallback to CB if no similar users
        cf_recs, is_cold_start_cf = cf_recommendations(
            target_user_id, user_movie_matrix, movies,
            top_n=top_n, min_common_movies=min_common_movies,
            top_k_similar=top_k_similar, genre_filter=genre_filter
        )
        
        if not is_cold_start_cf and len(cf_recs) > 0:
            return cf_recs, False
        
        # Fallback to content-based
        cb_recs = content_based_recommendations(
            target_user_id, user_movie_matrix, movies,
            top_n=top_n, genre_filter=genre_filter
        )
        
        if cb_recs:
            # Convert CB format to match CF format
            recommendations = [
                (rec[0], rec[1], rec[2] * 5.0, rec[3], [])  # Scale similarity to 0-5 range
                for rec in cb_recs
            ]
            return recommendations, True
        
        return [], True
    
    elif hybrid_method == 'mixed':
        # Get top recommendations from both approaches
        cf_recs, is_cold_start_cf = cf_recommendations(
            target_user_id, user_movie_matrix, movies,
            top_n=top_n, min_common_movies=min_common_movies,
            top_k_similar=top_k_similar, genre_filter=genre_filter
        )
        
        cb_recs = content_based_recommendations(
            target_user_id, user_movie_matrix, movies,
            top_n=top_n, genre_filter=genre_filter
        )
        
        # Combine and deduplicate
        movie_scores = defaultdict(lambda: {'cf_score': 0.0, 'cb_score': 0.0, 'genres': '', 'similar_users': []})
        
        # Add CF recommendations
        for movie_id, title, cf_score, genres, similar_users in cf_recs:
            movie_scores[movie_id]['cf_score'] = cf_score
            movie_scores[movie_id]['genres'] = genres
            movie_scores[movie_id]['similar_users'] = similar_users
        
        # Add CB recommendations
        for movie_id, title, cb_similarity, genres in cb_recs:
            cb_score = cb_similarity * 5.0  # Scale to 0-5 range
            movie_scores[movie_id]['cb_score'] = max(movie_scores[movie_id]['cb_score'], cb_score)
            if not movie_scores[movie_id]['genres']:
                movie_scores[movie_id]['genres'] = genres
        
        # Combine scores (weighted average)
        combined = []
        for movie_id, scores in movie_scores.items():
            combined_score = (scores['cf_score'] * cf_weight + scores['cb_score'] * cb_weight)
            if combined_score > 0:
                movie_info = movies[movies['movieId'] == movie_id]
                if len(movie_info) > 0:
                    title = movie_info.iloc[0]['title']
                    combined.append((
                        movie_id,
                        title,
                        combined_score,
                        scores['genres'],
                        scores['similar_users']
                    ))
        
        # Sort and return top N
        combined.sort(key=lambda x: x[2], reverse=True)
        recommendations = combined[:top_n]
        
        return recommendations, is_cold_start_cf and len(cb_recs) == 0
    
    else:  # weighted (default)
        # Get recommendations from both approaches
        cf_recs, is_cold_start_cf = cf_recommendations(
            target_user_id, user_movie_matrix, movies,
            top_n=top_n * 2,  # Get more to have better coverage
            min_common_movies=min_common_movies,
            top_k_similar=top_k_similar,
            genre_filter=None  # Apply filter later
        )
        
        cb_recs = content_based_recommendations(
            target_user_id, user_movie_matrix, movies,
            top_n=top_n * 2,
            genre_filter=None  # Apply filter later
        )
        
        # Combine scores using weighted average
        movie_scores = defaultdict(lambda: {
            'cf_score': 0.0,
            'cb_score': 0.0,
            'genres': '',
            'similar_users': [],
            'title': ''
        })
        
        # Process CF recommendations
        for movie_id, title, cf_score, genres, similar_users in cf_recs:
            movie_scores[movie_id]['cf_score'] = cf_score
            movie_scores[movie_id]['genres'] = genres
            movie_scores[movie_id]['similar_users'] = similar_users
            movie_scores[movie_id]['title'] = title
        
        # Process CB recommendations
        for movie_id, title, cb_similarity, genres in cb_recs:
            cb_score = cb_similarity * 5.0  # Scale similarity to 0-5 range
            movie_scores[movie_id]['cb_score'] = max(movie_scores[movie_id]['cb_score'], cb_score)
            if not movie_scores[movie_id]['genres']:
                movie_scores[movie_id]['genres'] = genres
            if not movie_scores[movie_id]['title']:
                movie_scores[movie_id]['title'] = title
        
        # Combine scores and apply genre filter
        combined = []
        for movie_id, scores in movie_scores.items():
            # Skip if genre filter doesn't match
            if genre_filter:
                if genre_filter.lower() not in scores['genres'].lower():
                    continue
            
            # Weighted combination
            if scores['cf_score'] > 0 or scores['cb_score'] > 0:
                combined_score = (scores['cf_score'] * cf_weight + scores['cb_score'] * cb_weight)
                combined.append((
                    movie_id,
                    scores['title'],
                    combined_score,
                    scores['genres'],
                    scores['similar_users']
                ))
        
        # Sort and return top N
        combined.sort(key=lambda x: x[2], reverse=True)
        recommendations = combined[:top_n]
        
        # Check if cold start
        is_cold_start = is_cold_start_cf and len(cb_recs) == 0
        
        if len(recommendations) == 0:
            # Still return empty or use fallback
            return recommendations, True
        
        return recommendations, is_cold_start
