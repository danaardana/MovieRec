"""
Metrics Calculation Module

This module provides functions to calculate various recommendation system metrics.
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Set
from collections import defaultdict


def calculate_rating_metrics(predictions: List[float], actuals: List[float]) -> Dict[str, float]:
    """
    Calculate rating prediction metrics (MAE, RMSE).
    
    Args:
        predictions: List of predicted ratings
        actuals: List of actual ratings
    
    Returns:
        Dictionary with metrics: {'mae': float, 'rmse': float}
    """
    if len(predictions) == 0 or len(actuals) == 0:
        return {'mae': 0.0, 'rmse': 0.0, 'count': 0}
    
    predictions = np.array(predictions)
    actuals = np.array(actuals)
    
    # Filter out invalid predictions (0 means couldn't predict)
    valid_mask = predictions > 0
    if valid_mask.sum() == 0:
        return {'mae': 0.0, 'rmse': 0.0, 'count': 0}
    
    valid_predictions = predictions[valid_mask]
    valid_actuals = actuals[valid_mask]
    
    mae = np.mean(np.abs(valid_predictions - valid_actuals))
    rmse = np.sqrt(np.mean((valid_predictions - valid_actuals) ** 2))
    
    return {
        'mae': float(mae),
        'rmse': float(rmse),
        'count': int(valid_mask.sum())
    }


def calculate_ranking_metrics(recommended_items: List[int], 
                              relevant_items: Set[int],
                              k: int = 10) -> Dict[str, float]:
    """
    Calculate ranking metrics (Precision@K, Recall@K, F1@K, NDCG@K).
    
    Args:
        recommended_items: List of recommended item IDs (top-K)
        relevant_items: Set of relevant item IDs (ground truth)
        k: Cutoff value for top-K metrics
    
    Returns:
        Dictionary with metrics: {'precision', 'recall', 'f1', 'ndcg'}
    """
    if len(relevant_items) == 0:
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'ndcg': 0.0
        }
    
    # Take top-K recommendations
    top_k_recommended = recommended_items[:k]
    
    # Calculate hits (items in both recommended and relevant)
    hits = set(top_k_recommended) & relevant_items
    
    # Precision@K: fraction of recommended items that are relevant
    precision = len(hits) / len(top_k_recommended) if len(top_k_recommended) > 0 else 0.0
    
    # Recall@K: fraction of relevant items that are recommended
    recall = len(hits) / len(relevant_items) if len(relevant_items) > 0 else 0.0
    
    # F1@K: harmonic mean of precision and recall
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    # NDCG@K: Normalized Discounted Cumulative Gain
    ndcg = calculate_ndcg(top_k_recommended, relevant_items, k)
    
    return {
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'ndcg': float(ndcg),
        'hits': len(hits),
        'relevant_count': len(relevant_items)
    }


def calculate_ndcg(recommended: List[int], relevant: Set[int], k: int) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain at K.
    
    Args:
        recommended: List of recommended item IDs
        relevant: Set of relevant item IDs
        k: Cutoff value
    
    Returns:
        NDCG@K value (0 to 1)
    """
    if len(relevant) == 0:
        return 0.0
    
    # Calculate DCG: sum of relevance scores divided by log2(position + 1)
    dcg = 0.0
    for i, item in enumerate(recommended[:k], 1):
        if item in relevant:
            dcg += 1.0 / np.log2(i + 1)
    
    # Calculate ideal DCG (IDCG): best possible DCG
    idcg = 0.0
    for i in range(min(len(relevant), k)):
        idcg += 1.0 / np.log2(i + 2)
    
    # NDCG = DCG / IDCG
    ndcg = dcg / idcg if idcg > 0 else 0.0
    return float(ndcg)


def calculate_diversity(recommendations: List[Tuple[int, str]], 
                       movies_df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate diversity metrics for recommendations.
    
    Args:
        recommendations: List of tuples (movie_id, title, ...)
        movies_df: DataFrame with movie information including genres
    
    Returns:
        Dictionary with diversity metrics
    """
    if len(recommendations) <= 1:
        return {
            'intra_list_diversity': 0.0,
            'genre_coverage': 0.0,
            'unique_genres': 0
        }
    
    # Extract movie IDs and get genres
    movie_ids = [rec[0] for rec in recommendations]
    genres_list = []
    all_genres = set()
    
    for movie_id in movie_ids:
        movie_info = movies_df[movies_df['movieId'] == movie_id]
        if len(movie_info) > 0:
            genres_str = movie_info.iloc[0]['genres']
            # Parse genres (format: "Action|Adventure|Sci-Fi")
            if pd.notna(genres_str):
                genres = set(genre.strip() for genre in str(genres_str).split('|') if genre.strip())
                genres_list.append(genres)
                all_genres.update(genres)
            else:
                genres_list.append(set())
    
    # Calculate intra-list diversity: average pairwise Jaccard distance
    if len(genres_list) > 1:
        diversity_scores = []
        for i in range(len(genres_list)):
            for j in range(i + 1, len(genres_list)):
                set1 = genres_list[i]
                set2 = genres_list[j]
                
                # Jaccard similarity
                intersection = len(set1 & set2)
                union = len(set1 | set2)
                similarity = intersection / union if union > 0 else 0.0
                
                # Jaccard distance (1 - similarity) for diversity
                diversity = 1.0 - similarity
                diversity_scores.append(diversity)
        
        intra_list_diversity = np.mean(diversity_scores) if diversity_scores else 0.0
    else:
        intra_list_diversity = 0.0
    
    # Genre coverage: number of unique genres in recommendations
    # Normalize by reasonable maximum (e.g., 20 unique genres is good diversity)
    max_reasonable_genres = 20
    genre_coverage = min(len(all_genres) / max_reasonable_genres, 1.0) if len(all_genres) > 0 else 0.0
    
    return {
        'intra_list_diversity': float(intra_list_diversity),
        'genre_coverage': float(min(genre_coverage, 1.0)),  # Cap at 1.0
        'unique_genres': len(all_genres)
    }


def calculate_coverage(predictions: Dict[int, float], 
                      all_items: Set[int]) -> float:
    """
    Calculate prediction coverage: percentage of items for which predictions can be made.
    
    Args:
        predictions: Dictionary of item_id -> predicted_rating
        all_items: Set of all items in the catalog
    
    Returns:
        Coverage percentage (0 to 1)
    """
    if len(all_items) == 0:
        return 0.0
    
    # Count items with valid predictions (prediction > 0)
    predictable_items = {item for item, pred in predictions.items() if pred > 0}
    coverage = len(predictable_items) / len(all_items)
    
    return float(coverage)
