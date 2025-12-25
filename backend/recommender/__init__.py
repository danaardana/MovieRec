"""
Recommender System Module

This package implements recommendation algorithms including:
- User-Based Collaborative Filtering
- Content-Based Filtering (genre-based)
- Hybrid approaches (combining CF and CB)
"""

from .collaborative_filtering import generate_recommendations
from .similarity import find_similar_users, pearson_correlation
from .prediction import predict_rating
from .content_based import content_based_recommendations
from .hybrid import hybrid_recommendations

__all__ = [
    'generate_recommendations',
    'find_similar_users',
    'pearson_correlation',
    'predict_rating',
    'content_based_recommendations',
    'hybrid_recommendations'
]

