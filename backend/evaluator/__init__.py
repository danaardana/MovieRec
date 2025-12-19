"""
Evaluation Module for MovieRec

This module provides performance evaluation metrics for the recommendation system.
"""

from .metrics import calculate_rating_metrics, calculate_ranking_metrics, calculate_diversity
from .evaluator import RecommenderEvaluator
from .fast_evaluator import FastRecommenderEvaluator

__all__ = [
    'calculate_rating_metrics',
    'calculate_ranking_metrics',
    'calculate_diversity',
    'RecommenderEvaluator',
    'FastRecommenderEvaluator'
]
