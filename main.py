"""
Main entry point for the Recommender System application.

This script allows users to get movie recommendations from the command line.
"""

import argparse
import sys
from recommender import (
    load_data,
    create_user_movie_matrix,
    generate_recommendations,
    display_recommendations
)


def main():
    """Main function to run the recommender system."""
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(
        description='Simple User-Based Collaborative Filtering Recommender System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --user 1
  python main.py --user 1 --top-n 20
  python main.py --user 1 --top-n 10 --min-common 10
        """
    )
    
    parser.add_argument(
        '--user',
        type=int,
        required=True,
        help='User ID to generate recommendations for'
    )
    
    parser.add_argument(
        '--top-n',
        type=int,
        default=10,
        help='Number of recommendations to generate (default: 10)'
    )
    
    parser.add_argument(
        '--min-common',
        type=int,
        default=5,
        help='Minimum number of common movies required for similarity calculation (default: 5)'
    )
    
    parser.add_argument(
        '--top-k-similar',
        type=int,
        default=50,
        help='Number of similar users to consider for predictions (default: 50)'
    )
    
    parser.add_argument(
        '--ratings',
        type=str,
        default='dataset/ratings.csv',
        help='Path to ratings.csv file (default: dataset/ratings.csv)'
    )
    
    parser.add_argument(
        '--movies',
        type=str,
        default='dataset/movies.csv',
        help='Path to movies.csv file (default: dataset/movies.csv)'
    )
    
    parser.add_argument(
        '--max-users',
        type=int,
        default=2000,
        help='Maximum number of users to load (default: 2000). Filters to most active users. Use 0 for all users (WARNING: may cause memory issues with large datasets)'
    )
    
    parser.add_argument(
        '--max-movies',
        type=int,
        default=2000,
        help='Maximum number of movies to load (default: 2000). Filters to most rated movies. Use 0 for all movies (WARNING: may cause memory issues with large datasets)'
    )
    
    parser.add_argument(
        '--download-images',
        action='store_true',
        help='Automatically download poster images for recommended movies'
    )
    
    parser.add_argument(
        '--image-dir',
        type=str,
        default='movie_posters',
        help='Directory to store movie poster images (default: movie_posters)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.top_n <= 0:
        print("Error: --top-n must be a positive integer")
        sys.exit(1)
    
    if args.min_common < 2:
        print("Error: --min-common must be at least 2")
        sys.exit(1)
    
    if args.top_k_similar <= 0:
        print("Error: --top-k-similar must be a positive integer")
        sys.exit(1)
    
    try:
        # Load data
        max_users = args.max_users if args.max_users > 0 else None
        max_movies = args.max_movies if args.max_movies > 0 else None
        ratings, movies = load_data(args.ratings, args.movies, max_users=max_users, max_movies=max_movies)
        
        # Create user-movie matrix
        user_movie_matrix = create_user_movie_matrix(ratings, use_sparse=True)
        
        # Generate recommendations
        recommendations = generate_recommendations(
            target_user_id=args.user,
            user_movie_matrix=user_movie_matrix,
            movies=movies,
            top_n=args.top_n,
            min_common_movies=args.min_common,
            top_k_similar=args.top_k_similar
        )
        
        # Display recommendations
        display_recommendations(
            recommendations,
            download_images=args.download_images,
            image_dir=args.image_dir
        )
        
    except FileNotFoundError as e:
        print(f"Error: Could not find data file: {e}")
        print("Please make sure the dataset files are in the correct location.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

