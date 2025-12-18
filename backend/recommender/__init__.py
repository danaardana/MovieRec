"""
Recommender System Module

This package implements User-Based Collaborative Filtering for movie recommendations.
"""

from .collaborative_filtering import generate_recommendations
from .similarity import find_similar_users, pearson_correlation
from .prediction import predict_rating

__all__ = [
    'generate_recommendations',
    'find_similar_users',
    'pearson_correlation',
    'predict_rating'
]

