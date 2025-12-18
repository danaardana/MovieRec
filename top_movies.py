"""
Script to display top movies from all users.

This script shows the most popular or highest-rated movies based on
ratings from all users in the dataset.
"""

import argparse
import sys
from recommender import load_data, get_top_movies, display_top_movies


def main():
    """Main function to display top movies."""
    parser = argparse.ArgumentParser(
        description='Display top movies from all users',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python top_movies.py
  python top_movies.py --top-n 30
  python top_movies.py --sort-by count
  python top_movies.py --top-n 20 --min-ratings 50 --sort-by average
        """
    )
    
    parser.add_argument(
        '--top-n',
        type=int,
        default=20,
        help='Number of top movies to display (default: 20)'
    )
    
    parser.add_argument(
        '--min-ratings',
        type=int,
        default=10,
        help='Minimum number of ratings required for a movie to be considered (default: 10)'
    )
    
    parser.add_argument(
        '--sort-by',
        type=str,
        choices=['average', 'count'],
        default='average',
        help='How to sort movies: "average" for highest rated, "count" for most popular (default: average)'
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
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.top_n <= 0:
        print("Error: --top-n must be a positive integer")
        sys.exit(1)
    
    if args.min_ratings < 1:
        print("Error: --min-ratings must be at least 1")
        sys.exit(1)
    
    try:
        # Load data
        ratings, movies = load_data(args.ratings, args.movies)
        
        # Get top movies
        top_movies = get_top_movies(
            ratings=ratings,
            movies=movies,
            top_n=args.top_n,
            min_ratings=args.min_ratings,
            sort_by=args.sort_by
        )
        
        # Display top movies
        display_top_movies(top_movies, sort_by=args.sort_by)
        
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

