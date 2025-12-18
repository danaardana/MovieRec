"""
Flask API Server for MovieRec

This server provides REST API endpoints for the movie recommendation system.
It connects the frontend (index.html) with the backend recommendation engine.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import get_recommendations

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Enable CORS for frontend requests

# Configuration
DATASET_PATH = 'dataset'
MAX_USERS = 2000
MAX_MOVIES = 2000


@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('.', 'index.html')


@app.route('/api/recommendations', methods=['POST'])
def recommendations():
    """
    Get movie recommendations API endpoint.
    
    Expected JSON body:
    {
        "user_id": int (required),
        "top_n": int (optional, default: 4),
        "genre": str (optional)
    }
    
    Returns:
    {
        "success": bool,
        "recommendations": [
            {
                "movie_id": int,
                "title": str,
                "predicted_rating": float,
                "genres": str,
                "image_path": str or null,
                "overview": str or null,
                "release_year": str or null
            },
            ...
        ],
        "message": str (if error)
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'user_id is required'
            }), 400
        
        # Validate user_id is a positive number
        try:
            user_id = int(user_id)
            if user_id < 1:
                return jsonify({
                    'success': False,
                    'message': 'User ID must be a positive number'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Invalid user_id format. Must be a positive number'
            }), 400
        
        top_n = data.get('top_n', 4)
        if top_n < 1 or top_n > 100:
            top_n = 4
        
        # Accept both 'genre' and 'category' (form uses 'category')
        genre = data.get('genre') or data.get('category')
        if genre:
            genre = str(genre).strip()
            if not genre:
                genre = None
        else:
            genre = None
        
        # Get recommendations
        recommendations = get_recommendations(
            user_id=int(user_id),
            top_n=int(top_n),
            genre=genre,
            ratings_path=os.path.join(DATASET_PATH, 'ratings.csv'),
            movies_path=os.path.join(DATASET_PATH, 'movies.csv'),
            max_users=MAX_USERS,
            max_movies=MAX_MOVIES,
            download_images=True,
            image_dir='movie_posters'
        )
        
        if not recommendations:
            # Get available user IDs from filtered dataset
            try:
                import pandas as pd
                ratings_sample = pd.read_csv(os.path.join(DATASET_PATH, 'ratings.csv'), nrows=500000)
                user_rating_counts = ratings_sample['userId'].value_counts()
                top_users = user_rating_counts.head(MAX_USERS).index.tolist()
                top_users_sorted = sorted(top_users)[:50]  # Get first 50 sorted user IDs
                
                if top_users_sorted:
                    available_str = ', '.join(map(str, top_users_sorted))
                    if len(top_users) > 50:
                        available_str += f'\n... and {len(top_users) - 50} more'
                else:
                    available_str = 'Unable to determine'
            except Exception as e:
                available_str = f'Unable to determine (Error: {str(e)})'
            
            # Provide more helpful error message
            error_msg = (
                f'No recommendations found for User ID {user_id}.\n\n'
                'Why only certain User IDs work:\n'
                '• System filters to top most active users\n'
                '• Only users with many ratings are included\n'
                '• User IDs are filtered by activity, not by ID number\n\n'
                'Available User IDs in dataset:\n'
                f'{available_str}\n\n'
                'Possible reasons for no recommendations:\n'
                '• User has no similar users with enough common movies\n'
                '• Genre filter too restrictive\n\n'
                'Try:\n'
                '• Use an available User ID from the list above\n'
                '• Removing genre filter'
            )
            return jsonify({
                'success': False,
                'message': error_msg,
                'recommendations': []
            }), 200
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        }), 200
        
    except Exception as e:
        # Provide user-friendly error message
        error_details = str(e)
        if 'not found' in error_details.lower():
            error_msg = f'User not found in the dataset.\n\nError: {error_details}'
        elif 'memory' in error_details.lower():
            error_msg = f'Memory error. Try reducing max_users or max_movies.\n\nError: {error_details}'
        else:
            error_msg = f'An error occurred while generating recommendations.\n\nError: {error_details}'
        
        return jsonify({
            'success': False,
            'message': error_msg,
            'recommendations': []
        }), 500


@app.route('/api/movie/<int:movie_id>/overview', methods=['GET'])
def get_movie_overview_api(movie_id):
    """
    Get movie overview/description for a specific movie.
    
    This endpoint can be used by the modal popup to fetch movie details.
    """
    try:
        from backend.utils import get_movie_overview
        
        # Get movie title from dataset (simplified - in production, use database)
        import pandas as pd
        movies = pd.read_csv(os.path.join(DATASET_PATH, 'movies.csv'))
        movie = movies[movies['movieId'] == movie_id]
        
        if len(movie) == 0:
            return jsonify({
                'success': False,
                'message': 'Movie not found'
            }), 404
        
        title = movie.iloc[0]['title']
        overview = get_movie_overview(title)
        
        return jsonify({
            'success': True,
            'movie_id': int(movie_id),
            'title': title,
            'overview': overview or 'No overview available'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/movie_posters/<path:filename>')
def serve_image(filename):
    """Serve movie poster images."""
    return send_from_directory('movie_posters', filename)


if __name__ == '__main__':
    print("="*70)
    print("MovieRec API Server")
    print("="*70)
    print("Server starting on http://localhost:5000")
    print("Frontend: http://localhost:5000/")
    print("API Endpoint: http://localhost:5000/api/recommendations")
    print("="*70)
    app.run(debug=True, host='0.0.0.0', port=5000)

