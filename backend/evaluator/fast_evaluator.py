"""
Fast Evaluator Module

Optimized version of the evaluator that only predicts ratings for test movies,
not all unrated movies. This is much faster for evaluation purposes.
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict
import time

from ..data_loader import load_data, create_user_movie_matrix
from ..recommender.similarity import find_similar_users
from ..recommender.prediction import predict_rating
from ..recommender.collaborative_filtering import get_popular_movies_fallback
from .metrics import (
    calculate_rating_metrics,
    calculate_ranking_metrics,
    calculate_diversity,
    calculate_coverage
)


class FastRecommenderEvaluator:
    """
    Fast evaluator that only predicts ratings for test movies (not all unrated movies).
    This is significantly faster than the standard evaluator.
    """
    
    def __init__(self, 
                 ratings_path: str = 'dataset/ratings.csv',
                 movies_path: str = 'dataset/movies.csv',
                 test_ratio: float = 0.2,
                 min_ratings_per_user: int = 5,
                 max_users: Optional[int] = None,
                 max_movies: Optional[int] = None,
                 random_seed: int = 42,
                 verbose: bool = True):
        """
        Initialize the fast evaluator.
        
        Args:
            ratings_path: Path to ratings.csv file
            movies_path: Path to movies.csv file
            test_ratio: Ratio of data to use for testing (0.0 to 1.0)
            min_ratings_per_user: Minimum ratings required per user for evaluation
            max_users: Maximum number of users to load (None for all)
            max_movies: Maximum number of movies to load (None for all)
            random_seed: Random seed for reproducibility
            verbose: Whether to print progress messages
        """
        self.ratings_path = ratings_path
        self.movies_path = movies_path
        self.test_ratio = test_ratio
        self.min_ratings_per_user = min_ratings_per_user
        self.max_users = max_users
        self.max_movies = max_movies
        self.random_seed = random_seed
        self.verbose = verbose
        
        # Set random seed
        np.random.seed(random_seed)
        
        # Data storage
        self.train_ratings = None
        self.test_ratings = None
        self.train_matrix = None
        self.movies_df = None
        
        # Results storage
        self.results = {}
        
        # Cache for similarity calculations
        self.similarity_cache = {}
    
    def _log(self, message: str):
        """Log message if verbose is enabled."""
        if self.verbose:
            print(message)
    
    def split_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Split ratings data into train and test sets."""
        self._log("Loading data for evaluation...")
        all_ratings, movies = load_data(
            self.ratings_path,
            self.movies_path,
            max_users=self.max_users,
            max_movies=self.max_movies
        )
        
        self.movies_df = movies
        
        # Filter users with minimum ratings
        self._log("Filtering users with minimum ratings...")
        user_rating_counts = all_ratings['userId'].value_counts()
        valid_users = user_rating_counts[user_rating_counts >= self.min_ratings_per_user].index
        all_ratings = all_ratings[all_ratings['userId'].isin(valid_users)]
        
        num_users = len(valid_users)
        num_ratings = len(all_ratings)
        
        self._log(f"Filtered to {num_users} users with at least {self.min_ratings_per_user} ratings ({num_ratings} total ratings)")
        
        # Warn if dataset is very large and no max_users/max_movies specified
        if self.max_users is None and num_users > 50000:
            self._log(f"\n⚠️  WARNING: Very large dataset detected ({num_users:,} users, {num_ratings:,} ratings)")
            self._log("   This will take a VERY long time to process!")
            self._log("   STRONGLY RECOMMENDED: Use --max-users and --max-movies to limit dataset size")
            self._log("   Example: --max-users 2000 --max-movies 2000")
            self._log("   This will make evaluation 100x+ faster while still providing good results.\n")
        
        # Optimized split using groupby (much faster than iterating)
        self._log("Splitting data into train/test sets (using optimized groupby)...")
        
        # Use groupby which is much more efficient than iterating per user
        groups = all_ratings.groupby('userId', sort=False)
        
        # For very large datasets, process in chunks with progress
        if num_users > 10000:
            self._log(f"Large dataset detected ({num_users:,} users). Processing in chunks...")
            chunk_size = 5000  # Smaller chunks for better progress indication
            train_chunks = []
            test_chunks = []
            
            processed = 0
            for user_id, user_group in groups:
                # Use deterministic seed based on user_id for reproducibility
                user_seed = (self.random_seed + int(user_id)) % (2**31)
                np.random.seed(user_seed)
                
                # Shuffle and split
                shuffled = user_group.sample(frac=1, random_state=user_seed).reset_index(drop=True)
                n_test = max(1, int(len(shuffled) * self.test_ratio))
                
                test_chunks.append(shuffled.head(n_test))
                train_chunks.append(shuffled.tail(len(shuffled) - n_test))
                
                processed += 1
                if processed % 10000 == 0:
                    self._log(f"  Processed {processed:,}/{num_users:,} users ({processed*100//num_users}%)...")
            
            train_ratings = pd.concat(train_chunks, ignore_index=True)
            test_ratings = pd.concat(test_chunks, ignore_index=True)
        else:
            # For smaller datasets, use direct groupby
            train_ratings_list = []
            test_ratings_list = []
            
            for user_id, user_group in groups:
                # Use deterministic seed based on user_id for reproducibility
                user_seed = (self.random_seed + int(user_id)) % (2**31)
                np.random.seed(user_seed)
                
                shuffled = user_group.sample(frac=1, random_state=user_seed).reset_index(drop=True)
                n_test = max(1, int(len(shuffled) * self.test_ratio))
                
                test_ratings_list.append(shuffled.head(n_test))
                train_ratings_list.append(shuffled.tail(len(shuffled) - n_test))
            
            train_ratings = pd.concat(train_ratings_list, ignore_index=True)
            test_ratings = pd.concat(test_ratings_list, ignore_index=True)
        
        self._log(f"Split data: {len(train_ratings):,} train ratings, {len(test_ratings):,} test ratings")
        
        self.train_ratings = train_ratings
        self.test_ratings = test_ratings
        
        return train_ratings, test_ratings
    
    def _get_similar_users_cached(self, user_id: int, min_common_movies: int) -> List[Tuple[int, float]]:
        """Get similar users with caching."""
        cache_key = (user_id, min_common_movies)
        if cache_key not in self.similarity_cache:
            # Temporarily disable verbose output for similarity calculation
            import sys
            from io import StringIO
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            try:
                similar_users = find_similar_users(
                    user_id, self.train_matrix, min_common_movies
                )
            finally:
                sys.stdout = old_stdout
            self.similarity_cache[cache_key] = similar_users
        return self.similarity_cache[cache_key]
    
    def _predict_ratings_for_movies(self,
                                    user_id: int,
                                    movie_ids: Set[int],
                                    similar_users: List[Tuple[int, float]],
                                    top_k_similar: int) -> Dict[int, float]:
        """
        Predict ratings for specific movies only (much faster than predicting all).
        
        Args:
            user_id: Target user ID
            movie_ids: Set of movie IDs to predict
            similar_users: List of (user_id, similarity) tuples
            top_k_similar: Number of similar users to consider
        
        Returns:
            Dictionary of movie_id -> predicted_rating
        """
        predictions = {}
        
        for movie_id in movie_ids:
            if movie_id in self.train_matrix.columns:
                pred_rating = predict_rating(
                    user_id, movie_id, self.train_matrix,
                    similar_users, top_k_similar
                )
                if pred_rating > 0:
                    predictions[movie_id] = pred_rating
        
        return predictions
    
    def _get_top_recommendations(self,
                                 user_id: int,
                                 test_movies: Set[int],
                                 predictions: Dict[int, float],
                                 top_n: int,
                                 similar_users: List[Tuple[int, float]],
                                 top_k_similar: int) -> List[Tuple[int, str, float, str, List[int]]]:
        """
        Get top-N recommendations from predictions.
        
        Note: This is a simplified version that only considers test movies and
        popular movies for ranking. For full recommendations, we'd need to predict
        all unrated movies, but that's too slow for evaluation.
        """
        recommendations = []
        
        # Sort predictions by rating
        sorted_predictions = sorted(predictions.items(), key=lambda x: x[1], reverse=True)
        
        # Get top-N from predictions
        for movie_id, pred_rating in sorted_predictions[:top_n]:
            movie_info = self.movies_df[self.movies_df['movieId'] == movie_id]
            if len(movie_info) > 0:
                title = movie_info.iloc[0]['title']
                genres = movie_info.iloc[0]['genres']
                recommendations.append((movie_id, title, pred_rating, genres, []))
        
        # If we don't have enough recommendations, fill with popular movies
        if len(recommendations) < top_n:
            # Get user's rated movies
            user_ratings = self.train_matrix.loc[user_id]
            rated_movies = set(user_ratings.dropna().index)
            
            # Get popular movies fallback
            popular = get_popular_movies_fallback(
                self.train_matrix, self.movies_df, user_id,
                top_n=top_n * 2, genre_filter=None, min_ratings=10
            )
            
            # Add popular movies that aren't already recommended
            recommended_ids = {rec[0] for rec in recommendations}
            for movie_id, title, avg_rating, genres, _ in popular:
                if len(recommendations) >= top_n:
                    break
                if movie_id not in recommended_ids and movie_id not in rated_movies:
                    recommendations.append((movie_id, title, avg_rating, genres, []))
        
        # Sort and take top-N
        recommendations.sort(key=lambda x: x[2], reverse=True)
        return recommendations[:top_n]
    
    def evaluate(self,
                 sample_users: Optional[int] = None,
                 top_n: int = 10,
                 min_common_movies: int = 5,
                 top_k_similar: int = 50,
                 rating_threshold: float = 3.5,
                 calculate_diversity_flag: bool = True) -> Dict:
        """
        Fast evaluation: only predict ratings for test movies.
        
        Args:
            sample_users: Number of users to evaluate (None for all)
            top_n: Number of recommendations to generate
            min_common_movies: Minimum common movies for similarity
            top_k_similar: Number of similar users to consider
            rating_threshold: Rating threshold for relevance
            calculate_diversity_flag: Whether to calculate diversity (can skip for speed)
        
        Returns:
            Dictionary with evaluation results
        """
        start_time = time.time()
        
        if self.train_ratings is None:
            self.split_data()
        
        # Create train matrix
        self._log("\nCreating training user-movie matrix...")
        self.train_matrix = create_user_movie_matrix(self.train_ratings, use_sparse=True)
        
        # Get users to evaluate
        test_users = self.test_ratings['userId'].unique()
        if sample_users is not None and sample_users < len(test_users):
            test_users = np.random.choice(test_users, size=sample_users, replace=False)
        
        self._log(f"\nEvaluating on {len(test_users)} users (fast mode: only predicting test movies)...")
        
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
        last_log_time = time.time()
        for idx, user_id in enumerate(test_users, 1):
            current_time = time.time()
            if current_time - last_log_time > 5:  # Log every 5 seconds
                elapsed = current_time - start_time
                rate = idx / elapsed
                remaining = (len(test_users) - idx) / rate if rate > 0 else 0
                self._log(f"  Progress: {idx}/{len(test_users)} users ({elapsed:.1f}s elapsed, ~{remaining:.1f}s remaining)...")
                last_log_time = current_time
            
            # Get test ratings for this user
            user_test_ratings = self.test_ratings[self.test_ratings['userId'] == user_id]
            
            if user_id not in self.train_matrix.index:
                cold_start_count += 1
                continue
            
            try:
                # Get similar users (with caching)
                similar_users = self._get_similar_users_cached(user_id, min_common_movies)
                
                if len(similar_users) == 0:
                    cold_start_count += 1
                    # Still try to get predictions using popular movies
                    user_test_movies = set(user_test_ratings['movieId'].values)
                    predictions = {}  # No predictions for cold start
                else:
                    # Get test movies for this user
                    user_test_movies = set(user_test_ratings['movieId'].values)
                    
                    # ONLY predict ratings for test movies (much faster!)
                    predictions = self._predict_ratings_for_movies(
                        user_id, user_test_movies, similar_users, top_k_similar
                    )
                
                # Get top recommendations (simplified - uses test movies + popular)
                recommendations = self._get_top_recommendations(
                    user_id, user_test_movies, predictions, top_n,
                    similar_users, top_k_similar
                )
                
                # Extract recommended movie IDs
                recommended_movie_ids = [rec[0] for rec in recommendations] if recommendations else []
                
                # Calculate diversity (optional, can skip for speed)
                if calculate_diversity_flag and recommendations:
                    diversity = calculate_diversity(recommendations, self.movies_df)
                    diversity_results.append(diversity)
                
                # Store predictions for coverage
                for rec in recommendations:
                    movie_id, _, pred_rating = rec[0], rec[1], rec[2]
                    coverage_predictions[movie_id] = max(coverage_predictions[movie_id], pred_rating)
                
                # Rating prediction metrics: use predictions for test movies
                user_predictions = []
                user_actuals = []
                
                for _, test_row in user_test_ratings.iterrows():
                    movie_id = test_row['movieId']
                    actual_rating = test_row['rating']
                    
                    if movie_id in predictions:
                        user_predictions.append(predictions[movie_id])
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
                if self.verbose:
                    print(f"  Error evaluating user {user_id}: {e}")
                continue
        
        elapsed_time = time.time() - start_time
        self._log(f"\nEvaluation completed in {elapsed_time:.2f} seconds")
        self._log("Calculating aggregate metrics...")
        
        # Rating metrics
        rating_metrics = calculate_rating_metrics(all_rating_predictions, all_rating_actuals)
        
        # Ranking metrics (average across users)
        ranking_metrics_agg = {
            f'precision@{top_n}': np.mean(ranking_results['precision']) if ranking_results['precision'] else 0.0,
            f'recall@{top_n}': np.mean(ranking_results['recall']) if ranking_results['recall'] else 0.0,
            f'f1@{top_n}': np.mean(ranking_results['f1']) if ranking_results['f1'] else 0.0,
            f'ndcg@{top_n}': np.mean(ranking_results['ndcg']) if ranking_results['ndcg'] else 0.0
        }
        
        # Diversity metrics (average)
        if diversity_results:
            diversity_metrics = {
                'avg_intra_list_diversity': np.mean([d['intra_list_diversity'] for d in diversity_results]),
                'avg_genre_coverage': np.mean([d['genre_coverage'] for d in diversity_results]),
                'avg_unique_genres': np.mean([d['unique_genres'] for d in diversity_results])
            }
        else:
            diversity_metrics = {
                'avg_intra_list_diversity': 0.0,
                'avg_genre_coverage': 0.0,
                'avg_unique_genres': 0.0
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
                'random_seed': self.random_seed,
                'fast_mode': True
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
            'evaluation_time_seconds': elapsed_time,
            'timestamp': datetime.now().isoformat()
        }
        
        return self.results
    
    def save_results(self, output_dir: str = 'evaluation_results') -> Dict[str, str]:
        """Save evaluation results to multiple formats."""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f'evaluation_fast_{timestamp}'
        
        saved_files = {}
        
        # 1. Save to JSON
        json_path = os.path.join(output_dir, f'{base_name}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        saved_files['json'] = json_path
        
        # 2. Save to CSV
        csv_path = os.path.join(output_dir, f'{base_name}_metrics.csv')
        self._save_csv(csv_path)
        saved_files['csv'] = csv_path
        
        # 3. Save to log file
        log_path = os.path.join(output_dir, f'{base_name}.log')
        self._save_log(log_path)
        saved_files['log'] = log_path
        
        # 4. Save to text file
        txt_path = os.path.join(output_dir, f'{base_name}.txt')
        self._save_text(txt_path)
        saved_files['txt'] = txt_path
        
        self._log(f"\nResults saved to:")
        for format_type, path in saved_files.items():
            self._log(f"  {format_type.upper()}: {path}")
        
        return saved_files
    
    def _save_csv(self, csv_path: str):
        """Save metrics to CSV format."""
        rows = []
        
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
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler() if self.verbose else logging.NullHandler()
            ]
        )
        
        logger = logging.getLogger()
        logger.info("=" * 80)
        logger.info("MOVIE RECOMMENDATION SYSTEM EVALUATION RESULTS (FAST MODE)")
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
        logger.info(f"EVALUATION TIME: {self.results['evaluation_time_seconds']:.2f} seconds")
        
        logger.info(f"\nEvaluation completed at: {self.results['timestamp']}")
        logger.info("=" * 80)
    
    def _save_text(self, txt_path: str):
        """Save results to human-readable text file."""
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("MOVIE RECOMMENDATION SYSTEM EVALUATION RESULTS (FAST MODE)\n")
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
            f.write(f"EVALUATION TIME: {self.results['evaluation_time_seconds']:.2f} seconds\n")
            
            f.write(f"\nEvaluation completed at: {self.results['timestamp']}\n")
            f.write("=" * 80 + "\n")
