"""
Main Evaluator Module

This module provides the RecommenderEvaluator class for comprehensive system evaluation.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict

from ..data_loader import load_data, create_user_movie_matrix
from ..recommender import generate_recommendations
from .metrics import (
    calculate_rating_metrics,
    calculate_ranking_metrics,
    calculate_diversity,
    calculate_coverage
)


class RecommenderEvaluator:
    """
    Evaluator class for recommendation system performance evaluation.
    
    Supports train-test split evaluation and outputs results to multiple formats:
    - Log files (.log, .txt)
    - CSV files (structured metrics)
    - JSON files (programmatic access)
    """
    
    def __init__(self, 
                 ratings_path: str = 'dataset/ratings.csv',
                 movies_path: str = 'dataset/movies.csv',
                 test_ratio: float = 0.2,
                 min_ratings_per_user: int = 5,
                 max_users: Optional[int] = None,
                 max_movies: Optional[int] = None,
                 random_seed: int = 42):
        """
        Initialize the evaluator.
        
        Args:
            ratings_path: Path to ratings.csv file
            movies_path: Path to movies.csv file
            test_ratio: Ratio of data to use for testing (0.0 to 1.0)
            min_ratings_per_user: Minimum ratings required per user for evaluation
            max_users: Maximum number of users to load (None for all)
            max_movies: Maximum number of movies to load (None for all)
            random_seed: Random seed for reproducibility
        """
        self.ratings_path = ratings_path
        self.movies_path = movies_path
        self.test_ratio = test_ratio
        self.min_ratings_per_user = min_ratings_per_user
        self.max_users = max_users
        self.max_movies = max_movies
        self.random_seed = random_seed
        
        # Set random seed
        np.random.seed(random_seed)
        
        # Data storage
        self.train_ratings = None
        self.test_ratings = None
        self.train_matrix = None
        self.movies_df = None
        
        # Results storage
        self.results = {}
    
    def split_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split ratings data into train and test sets.
        
        Returns:
            Tuple of (train_ratings, test_ratings)
        """
        print("Loading data for evaluation...")
        all_ratings, movies = load_data(
            self.ratings_path,
            self.movies_path,
            max_users=self.max_users,
            max_movies=self.max_movies
        )
        
        self.movies_df = movies
        
        # Filter users with minimum ratings
        user_rating_counts = all_ratings['userId'].value_counts()
        valid_users = user_rating_counts[user_rating_counts >= self.min_ratings_per_user].index
        all_ratings = all_ratings[all_ratings['userId'].isin(valid_users)]
        
        print(f"Filtered to {len(valid_users)} users with at least {self.min_ratings_per_user} ratings")
        
        # Split data: for each user, randomly assign some ratings to test set
        train_ratings_list = []
        test_ratings_list = []
        
        for user_id in valid_users:
            user_ratings = all_ratings[all_ratings['userId'] == user_id].copy()
            
            # Shuffle
            user_ratings = user_ratings.sample(frac=1, random_state=self.random_seed).reset_index(drop=True)
            
            # Split
            n_test = max(1, int(len(user_ratings) * self.test_ratio))
            test_ratings_user = user_ratings.head(n_test)
            train_ratings_user = user_ratings.tail(len(user_ratings) - n_test)
            
            train_ratings_list.append(train_ratings_user)
            test_ratings_list.append(test_ratings_user)
        
        train_ratings = pd.concat(train_ratings_list, ignore_index=True)
        test_ratings = pd.concat(test_ratings_list, ignore_index=True)
        
        print(f"Split data: {len(train_ratings)} train ratings, {len(test_ratings)} test ratings")
        
        self.train_ratings = train_ratings
        self.test_ratings = test_ratings
        
        return train_ratings, test_ratings
    
    def evaluate(self,
                 sample_users: Optional[int] = None,
                 top_n: int = 10,
                 min_common_movies: int = 5,
                 top_k_similar: int = 50,
                 rating_threshold: float = 3.5) -> Dict:
        """
        Evaluate the recommendation system.
        
        Args:
            sample_users: Number of users to evaluate (None for all)
            top_n: Number of recommendations to generate
            min_common_movies: Minimum common movies for similarity
            top_k_similar: Number of similar users to consider
            rating_threshold: Rating threshold for relevance (>= threshold is relevant)
        
        Returns:
            Dictionary with evaluation results
        """
        if self.train_ratings is None:
            self.split_data()
        
        # Create train matrix
        print("\nCreating training user-movie matrix...")
        self.train_matrix = create_user_movie_matrix(self.train_ratings, use_sparse=True)
        
        # Get users to evaluate
        test_users = self.test_ratings['userId'].unique()
        if sample_users is not None and sample_users < len(test_users):
            test_users = np.random.choice(test_users, size=sample_users, replace=False)
        
        print(f"\nEvaluating on {len(test_users)} users...")
        
        # Aggregate results
        all_rating_predictions = []
        all_rating_actuals = []
        
        ranking_results = {
            'precision': [],
            'recall': [],
            'f1': [],
            'ndcg': []
        }
        
        diversity_results = []
        cold_start_count = 0
        coverage_predictions = defaultdict(float)
        all_items = set(self.train_matrix.columns)
        
        # Evaluate each user
        for idx, user_id in enumerate(test_users, 1):
            if idx % 10 == 0:
                print(f"  Processing user {idx}/{len(test_users)}...")
            
            # Get test ratings for this user
            user_test_ratings = self.test_ratings[self.test_ratings['userId'] == user_id]
            
            if user_id not in self.train_matrix.index:
                cold_start_count += 1
                continue
            
            # Generate recommendations
            try:
                recommendations, is_cold_start = generate_recommendations(
                    target_user_id=user_id,
                    user_movie_matrix=self.train_matrix,
                    movies=self.movies_df,
                    top_n=top_n,
                    min_common_movies=min_common_movies,
                    top_k_similar=top_k_similar,
                    genre_filter=None
                )
                
                if is_cold_start:
                    cold_start_count += 1
                
                # Extract recommended movie IDs
                if len(recommendations) > 0:
                    recommended_movie_ids = [rec[0] for rec in recommendations]
                    
                    # Calculate diversity
                    diversity = calculate_diversity(recommendations, self.movies_df)
                    diversity_results.append(diversity)
                    
                    # Store predictions for coverage
                    for rec in recommendations:
                        movie_id, _, pred_rating = rec[0], rec[1], rec[2]
                        coverage_predictions[movie_id] = max(coverage_predictions[movie_id], pred_rating)
                else:
                    recommended_movie_ids = []
                    diversity_results.append({
                        'intra_list_diversity': 0.0,
                        'genre_coverage': 0.0,
                        'unique_genres': 0
                    })
                
                # Rating prediction metrics: predict ratings for test movies
                user_test_movies = set(user_test_ratings['movieId'].values)
                user_predictions = []
                user_actuals = []
                
                for _, test_row in user_test_ratings.iterrows():
                    movie_id = test_row['movieId']
                    actual_rating = test_row['rating']
                    
                    # Try to find predicted rating in recommendations
                    predicted_rating = 0.0
                    for rec in recommendations:
                        if rec[0] == movie_id:
                            predicted_rating = rec[2]
                            break
                    
                    if predicted_rating > 0:
                        user_predictions.append(predicted_rating)
                        user_actuals.append(actual_rating)
                
                all_rating_predictions.extend(user_predictions)
                all_rating_actuals.extend(user_actuals)
                
                # Ranking metrics: relevant items are test movies with rating >= threshold
                relevant_movies = set(
                    user_test_ratings[user_test_ratings['rating'] >= rating_threshold]['movieId'].values
                )
                
                if len(relevant_movies) > 0:
                    ranking_metrics = calculate_ranking_metrics(
                        recommended_movie_ids,
                        relevant_movies,
                        k=top_n
                    )
                    
                    ranking_results['precision'].append(ranking_metrics['precision'])
                    ranking_results['recall'].append(ranking_metrics['recall'])
                    ranking_results['f1'].append(ranking_metrics['f1'])
                    ranking_results['ndcg'].append(ranking_metrics['ndcg'])
            
            except Exception as e:
                print(f"  Error evaluating user {user_id}: {e}")
                continue
        
        # Calculate aggregate metrics
        print("\nCalculating aggregate metrics...")
        
        # Rating metrics
        rating_metrics = calculate_rating_metrics(all_rating_predictions, all_rating_actuals)
        
        # Ranking metrics (average across users)
        ranking_metrics_agg = {
            'precision@' + str(top_n): np.mean(ranking_results['precision']) if ranking_results['precision'] else 0.0,
            'recall@' + str(top_n): np.mean(ranking_results['recall']) if ranking_results['recall'] else 0.0,
            'f1@' + str(top_n): np.mean(ranking_results['f1']) if ranking_results['f1'] else 0.0,
            'ndcg@' + str(top_n): np.mean(ranking_results['ndcg']) if ranking_results['ndcg'] else 0.0
        }
        
        # Diversity metrics (average)
        diversity_metrics = {
            'avg_intra_list_diversity': np.mean([d['intra_list_diversity'] for d in diversity_results]) if diversity_results else 0.0,
            'avg_genre_coverage': np.mean([d['genre_coverage'] for d in diversity_results]) if diversity_results else 0.0,
            'avg_unique_genres': np.mean([d['unique_genres'] for d in diversity_results]) if diversity_results else 0.0
        }
        
        # Coverage
        coverage = calculate_coverage(coverage_predictions, all_items)
        
        # Compile results
        self.results = {
            'evaluation_config': {
                'test_ratio': self.test_ratio,
                'sample_users': sample_users,
                'top_n': top_n,
                'min_common_movies': min_common_movies,
                'top_k_similar': top_k_similar,
                'rating_threshold': rating_threshold,
                'random_seed': self.random_seed
            },
            'dataset_info': {
                'train_ratings_count': len(self.train_ratings),
                'test_ratings_count': len(self.test_ratings),
                'total_users': len(test_users),
                'evaluated_users': len(test_users) - cold_start_count
            },
            'rating_metrics': rating_metrics,
            'ranking_metrics': ranking_metrics_agg,
            'diversity_metrics': diversity_metrics,
            'coverage': coverage,
            'cold_start_rate': cold_start_count / len(test_users) if len(test_users) > 0 else 0.0,
            'timestamp': datetime.now().isoformat()
        }
        
        return self.results
    
    def save_results(self, output_dir: str = 'evaluation_results') -> Dict[str, str]:
        """
        Save evaluation results to multiple formats.
        
        Args:
            output_dir: Directory to save results
        
        Returns:
            Dictionary with paths to saved files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f'evaluation_{timestamp}'
        
        saved_files = {}
        
        # 1. Save to JSON
        json_path = os.path.join(output_dir, f'{base_name}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        saved_files['json'] = json_path
        
        # 2. Save to CSV (structured metrics)
        csv_path = os.path.join(output_dir, f'{base_name}_metrics.csv')
        self._save_csv(csv_path)
        saved_files['csv'] = csv_path
        
        # 3. Save to log file
        log_path = os.path.join(output_dir, f'{base_name}.log')
        self._save_log(log_path)
        saved_files['log'] = log_path
        
        # 4. Save to text file (human-readable)
        txt_path = os.path.join(output_dir, f'{base_name}.txt')
        self._save_text(txt_path)
        saved_files['txt'] = txt_path
        
        print(f"\nResults saved to:")
        for format_type, path in saved_files.items():
            print(f"  {format_type.upper()}: {path}")
        
        return saved_files
    
    def _save_csv(self, csv_path: str):
        """Save metrics to CSV format."""
        rows = []
        
        # Add each metric as a row
        for category, metrics in self.results.items():
            if isinstance(metrics, dict) and category not in ['evaluation_config', 'timestamp']:
                for metric_name, metric_value in metrics.items():
                    rows.append({
                        'category': category,
                        'metric': metric_name,
                        'value': metric_value
                    })
        
        df = pd.DataFrame(rows)
        df.to_csv(csv_path, index=False)
    
    def _save_log(self, log_path: str):
        """Save detailed results to log file."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        logger = logging.getLogger()
        logger.info("=" * 80)
        logger.info("MOVIE RECOMMENDATION SYSTEM EVALUATION RESULTS")
        logger.info("=" * 80)
        
        logger.info("\nEVALUATION CONFIGURATION:")
        for key, value in self.results['evaluation_config'].items():
            logger.info(f"  {key}: {value}")
        
        logger.info("\nDATASET INFORMATION:")
        for key, value in self.results['dataset_info'].items():
            logger.info(f"  {key}: {value}")
        
        logger.info("\nRATING PREDICTION METRICS:")
        for key, value in self.results['rating_metrics'].items():
            logger.info(f"  {key}: {value:.4f}")
        
        logger.info("\nRANKING METRICS:")
        for key, value in self.results['ranking_metrics'].items():
            logger.info(f"  {key}: {value:.4f}")
        
        logger.info("\nDIVERSITY METRICS:")
        for key, value in self.results['diversity_metrics'].items():
            logger.info(f"  {key}: {value:.4f}")
        
        logger.info(f"\nCOVERAGE: {self.results['coverage']:.4f}")
        logger.info(f"COLD START RATE: {self.results['cold_start_rate']:.4f}")
        
        logger.info(f"\nEvaluation completed at: {self.results['timestamp']}")
        logger.info("=" * 80)
    
    def _save_text(self, txt_path: str):
        """Save results to human-readable text file."""
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("MOVIE RECOMMENDATION SYSTEM EVALUATION RESULTS\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("EVALUATION CONFIGURATION:\n")
            for key, value in self.results['evaluation_config'].items():
                f.write(f"  {key}: {value}\n")
            
            f.write("\nDATASET INFORMATION:\n")
            for key, value in self.results['dataset_info'].items():
                f.write(f"  {key}: {value}\n")
            
            f.write("\nRATING PREDICTION METRICS:\n")
            for key, value in self.results['rating_metrics'].items():
                f.write(f"  {key}: {value:.4f}\n")
            
            f.write("\nRANKING METRICS:\n")
            for key, value in self.results['ranking_metrics'].items():
                f.write(f"  {key}: {value:.4f}\n")
            
            f.write("\nDIVERSITY METRICS:\n")
            for key, value in self.results['diversity_metrics'].items():
                f.write(f"  {key}: {value:.4f}\n")
            
            f.write(f"\nCOVERAGE: {self.results['coverage']:.4f}\n")
            f.write(f"COLD START RATE: {self.results['cold_start_rate']:.4f}\n")
            
            f.write(f"\nEvaluation completed at: {self.results['timestamp']}\n")
            f.write("=" * 80 + "\n")
