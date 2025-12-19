"""
Evaluation Script for MovieRec Recommendation System

This script performs comprehensive evaluation of the recommendation system
and saves results to multiple formats (JSON, CSV, LOG, TXT).

Usage:
    python evaluate_system.py [options]

Examples:
    # Basic evaluation with default settings
    python evaluate_system.py

    # Evaluate on 100 users with top-10 recommendations
    python evaluate_system.py --sample-users 100 --top-n 10

    # Custom test ratio and output directory
    python evaluate_system.py --test-ratio 0.3 --output-dir results
"""

import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.evaluator import RecommenderEvaluator
from backend.evaluator.fast_evaluator import FastRecommenderEvaluator


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate MovieRec recommendation system performance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--ratings-path',
        type=str,
        default='dataset/ratings.csv',
        help='Path to ratings.csv file (default: dataset/ratings.csv)'
    )
    
    parser.add_argument(
        '--movies-path',
        type=str,
        default='dataset/movies.csv',
        help='Path to movies.csv file (default: dataset/movies.csv)'
    )
    
    parser.add_argument(
        '--test-ratio',
        type=float,
        default=0.2,
        help='Ratio of data to use for testing (default: 0.2, i.e., 20%%)'
    )
    
    parser.add_argument(
        '--sample-users',
        type=int,
        default=None,
        help='Number of users to evaluate (default: all users)'
    )
    
    parser.add_argument(
        '--top-n',
        type=int,
        default=10,
        help='Number of recommendations to generate per user (default: 10)'
    )
    
    parser.add_argument(
        '--min-ratings-per-user',
        type=int,
        default=5,
        help='Minimum ratings required per user for evaluation (default: 5)'
    )
    
    parser.add_argument(
        '--min-common-movies',
        type=int,
        default=5,
        help='Minimum common movies for similarity calculation (default: 5)'
    )
    
    parser.add_argument(
        '--top-k-similar',
        type=int,
        default=50,
        help='Number of similar users to consider for predictions (default: 50)'
    )
    
    parser.add_argument(
        '--rating-threshold',
        type=float,
        default=3.5,
        help='Rating threshold for relevance (>= threshold is relevant, default: 3.5)'
    )
    
    parser.add_argument(
        '--max-users',
        type=int,
        default=None,
        help='Maximum number of users to load from dataset (default: all)'
    )
    
    parser.add_argument(
        '--max-movies',
        type=int,
        default=None,
        help='Maximum number of movies to load from dataset (default: all)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='evaluation_results',
        help='Directory to save evaluation results (default: evaluation_results)'
    )
    
    parser.add_argument(
        '--random-seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    
    parser.add_argument(
        '--fast-mode',
        action='store_true',
        default=True,
        help='Use fast evaluation mode (only predict test movies, much faster) (default: True)'
    )
    
    parser.add_argument(
        '--standard-mode',
        action='store_true',
        default=False,
        help='Use standard evaluation mode (predict all unrated movies, slower but more accurate)'
    )
    
    parser.add_argument(
        '--skip-diversity',
        action='store_true',
        default=False,
        help='Skip diversity calculation for even faster evaluation (fast mode only)'
    )
    
    args = parser.parse_args()
    
    # Fast mode is default unless standard-mode is explicitly requested
    use_fast_mode = args.fast_mode and not args.standard_mode
    
    # Validate arguments
    if not 0 < args.test_ratio < 1:
        print("Error: test_ratio must be between 0 and 1")
        sys.exit(1)
    
    if not os.path.exists(args.ratings_path):
        print(f"Error: Ratings file not found: {args.ratings_path}")
        sys.exit(1)
    
    if not os.path.exists(args.movies_path):
        print(f"Error: Movies file not found: {args.movies_path}")
        sys.exit(1)
    
    # Print configuration
    print("=" * 80)
    print("MOVIE RECOMMENDATION SYSTEM EVALUATION")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Ratings file: {args.ratings_path}")
    print(f"  Movies file: {args.movies_path}")
    print(f"  Test ratio: {args.test_ratio}")
    print(f"  Sample users: {args.sample_users if args.sample_users else 'All'}")
    print(f"  Top-N recommendations: {args.top_n}")
    print(f"  Min ratings per user: {args.min_ratings_per_user}")
    print(f"  Min common movies: {args.min_common_movies}")
    print(f"  Top-K similar users: {args.top_k_similar}")
    print(f"  Rating threshold: {args.rating_threshold}")
    max_users_display = args.max_users if args.max_users else 'All'
    max_movies_display = args.max_movies if args.max_movies else 'All'
    print(f"  Max users: {max_users_display}")
    print(f"  Max movies: {max_movies_display}")
    
    if not args.max_users or not args.max_movies:
        print("\n⚠️  NOTE: For large datasets, consider using --max-users and --max-movies")
        print("   Example: --max-users 2000 --max-movies 2000 (much faster!)")
    print(f"  Output directory: {args.output_dir}")
    print(f"  Random seed: {args.random_seed}")
    print(f"  Evaluation mode: {'FAST (recommended)' if use_fast_mode else 'STANDARD (slower)'}")
    if use_fast_mode and args.skip_diversity:
        print(f"  Skip diversity: Yes (faster)")
    print("=" * 80)
    print()
    
    # Initialize evaluator
    if use_fast_mode:
        evaluator = FastRecommenderEvaluator(
            ratings_path=args.ratings_path,
            movies_path=args.movies_path,
            test_ratio=args.test_ratio,
            min_ratings_per_user=args.min_ratings_per_user,
            max_users=args.max_users,
            max_movies=args.max_movies,
            random_seed=args.random_seed,
            verbose=True
        )
    else:
        evaluator = RecommenderEvaluator(
            ratings_path=args.ratings_path,
            movies_path=args.movies_path,
            test_ratio=args.test_ratio,
            min_ratings_per_user=args.min_ratings_per_user,
            max_users=args.max_users,
            max_movies=args.max_movies,
            random_seed=args.random_seed
        )
    
    # Run evaluation
    try:
        if use_fast_mode:
            results = evaluator.evaluate(
                sample_users=args.sample_users,
                top_n=args.top_n,
                min_common_movies=args.min_common_movies,
                top_k_similar=args.top_k_similar,
                rating_threshold=args.rating_threshold,
                calculate_diversity_flag=not args.skip_diversity
            )
        else:
            results = evaluator.evaluate(
                sample_users=args.sample_users,
                top_n=args.top_n,
                min_common_movies=args.min_common_movies,
                top_k_similar=args.top_k_similar,
                rating_threshold=args.rating_threshold
            )
        
        # Save results
        saved_files = evaluator.save_results(output_dir=args.output_dir)
        
        # Print summary
        print("\n" + "=" * 80)
        print("EVALUATION SUMMARY")
        print("=" * 80)
        print(f"\nRating Prediction Metrics:")
        print(f"  MAE:  {results['rating_metrics']['mae']:.4f}")
        print(f"  RMSE: {results['rating_metrics']['rmse']:.4f}")
        print(f"  Valid predictions: {results['rating_metrics']['count']}")
        
        print(f"\nRanking Metrics (Top-{args.top_n}):")
        print(f"  Precision@{args.top_n}: {results['ranking_metrics'][f'precision@{args.top_n}']:.4f}")
        print(f"  Recall@{args.top_n}:    {results['ranking_metrics'][f'recall@{args.top_n}']:.4f}")
        print(f"  F1@{args.top_n}:        {results['ranking_metrics'][f'f1@{args.top_n}']:.4f}")
        print(f"  NDCG@{args.top_n}:      {results['ranking_metrics'][f'ndcg@{args.top_n}']:.4f}")
        
        print(f"\nDiversity Metrics:")
        print(f"  Intra-list diversity: {results['diversity_metrics']['avg_intra_list_diversity']:.4f}")
        print(f"  Genre coverage:       {results['diversity_metrics']['avg_genre_coverage']:.4f}")
        print(f"  Avg unique genres:    {results['diversity_metrics']['avg_unique_genres']:.2f}")
        
        print(f"\nOther Metrics:")
        print(f"  Coverage:        {results['coverage']:.4f}")
        print(f"  Cold start rate: {results['cold_start_rate']:.4f}")
        
        print("\n" + "=" * 80)
        print("Evaluation completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nError during evaluation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
