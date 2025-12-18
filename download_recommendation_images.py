"""
Standalone script to download images for recommended movies.

This script demonstrates how to use the image_downloader module
to download poster images for movies from recommendations.
"""

import argparse
import sys
from recommender import load_data, create_user_movie_matrix, generate_recommendations
from image_downloader import download_movie_images_batch


def main():
    """Main function to download images for recommended movies."""
    parser = argparse.ArgumentParser(
        description='Download poster images for recommended movies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_recommendation_images.py --user 189614
  python download_recommendation_images.py --user 189614 --top-n 10
  python download_recommendation_images.py --user 189614 --top-n 5 --output-dir my_posters
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
        help='Number of recommendations (default: 10)'
    )
    
    parser.add_argument(
        '--min-common',
        type=int,
        default=5,
        help='Minimum common movies for similarity (default: 5)'
    )
    
    parser.add_argument(
        '--max-users',
        type=int,
        default=2000,
        help='Maximum number of users to load (default: 2000)'
    )
    
    parser.add_argument(
        '--max-movies',
        type=int,
        default=2000,
        help='Maximum number of movies to load (default: 2000)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='movie_posters',
        help='Directory to save images (default: movie_posters)'
    )
    
    parser.add_argument(
        '--ratings',
        type=str,
        default='dataset/ratings.csv',
        help='Path to ratings.csv file'
    )
    
    parser.add_argument(
        '--movies',
        type=str,
        default='dataset/movies.csv',
        help='Path to movies.csv file'
    )
    
    args = parser.parse_args()
    
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
            top_k_similar=50
        )
        
        if len(recommendations) == 0:
            print("No recommendations found.")
            sys.exit(1)
        
        # Extract movie titles
        movie_titles = [title for _, title, _ in recommendations]
        
        # Download images
        download_movie_images_batch(
            movie_titles,
            output_dir=args.output_dir,
            verbose=True
        )
        
    except FileNotFoundError as e:
        print(f"Error: Could not find data file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

