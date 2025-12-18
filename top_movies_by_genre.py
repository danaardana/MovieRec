"""
Script to display top movies by genre.

This script shows the most popular or highest-rated movies for a specific genre.
Can also automatically download poster images for the movies.
"""

import argparse
import sys
from recommender import load_data, get_top_movies_by_genre, display_top_movies_by_genre, list_available_genres


def main():
    """Main function to display top movies by genre."""
    parser = argparse.ArgumentParser(
        description='Display top movies by genre',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python top_movies_by_genre.py --genre Action
  python top_movies_by_genre.py --genre Comedy --top-n 15
  python top_movies_by_genre.py --genre Drama --min-ratings 100 --sort-by count
  python top_movies_by_genre.py --genre Action --top-n 10 --download-images
  python top_movies_by_genre.py --list-genres
        """
    )
    
    parser.add_argument(
        '--genre',
        type=str,
        default=None,
        help='Genre to filter by (e.g., Action, Comedy, Drama, Horror, Sci-Fi)'
    )
    
    parser.add_argument(
        '--list-genres',
        action='store_true',
        help='List all available genres in the dataset'
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
        help='Minimum number of ratings required (default: 10)'
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
    
    parser.add_argument(
        '--download-images',
        action='store_true',
        help='Automatically download poster images for the top movies'
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
    
    if args.min_ratings < 1:
        print("Error: --min-ratings must be at least 1")
        sys.exit(1)
    
    try:
        # Load data
        ratings, movies = load_data(args.ratings, args.movies)
        
        # List genres if requested
        if args.list_genres:
            genres = list_available_genres(movies)
            print("\nAvailable genres in the dataset:")
            print("="*50)
            for i, genre in enumerate(genres, 1):
                print(f"{i:2d}. {genre}")
            print("="*50)
            print(f"\nTotal: {len(genres)} genres")
            print("\nExample usage:")
            print(f"  python top_movies_by_genre.py --genre {genres[0] if genres else 'Action'} --top-n 10")
            sys.exit(0)
        
        # Check if genre is provided
        if not args.genre:
            print("Error: --genre is required (or use --list-genres to see available genres)")
            print("\nAvailable genres:")
            genres = list_available_genres(movies)
            for genre in genres[:10]:  # Show first 10
                print(f"  - {genre}")
            print(f"  ... and {len(genres) - 10} more (use --list-genres to see all)")
            sys.exit(1)
        
        # Get top movies by genre
        top_movies = get_top_movies_by_genre(
            ratings=ratings,
            movies=movies,
            genre=args.genre,
            top_n=args.top_n,
            min_ratings=args.min_ratings,
            sort_by=args.sort_by
        )
        
        # Display top movies
        display_top_movies_by_genre(top_movies, genre=args.genre, sort_by=args.sort_by)
        
        # Download images if requested
        if args.download_images and len(top_movies) > 0:
            try:
                from image_downloader import download_movie_images_batch
                
                # Extract movie titles
                movie_titles = top_movies['title'].tolist()
                
                print(f"\n{'='*80}")
                print("Downloading poster images...")
                print(f"{'='*80}")
                
                # Download images
                download_movie_images_batch(
                    movie_titles,
                    output_dir=args.image_dir,
                    verbose=True
                )
            except ImportError:
                print("\nWarning: image_downloader module not found. Skipping image download.")
            except Exception as e:
                print(f"\nWarning: Could not download images: {e}")
                import traceback
                traceback.print_exc()
        
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

