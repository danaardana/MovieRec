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
        "genre": str (optional),
        "cf_weight": float (optional, default: 0.7) - Weight for Collaborative Filtering,
        "cb_weight": float (optional, default: 0.3) - Weight for Content-Based,
        "hybrid_method": str (optional, default: "weighted") - Hybrid method: "weighted", "mixed", or "switching"
    }
    
    Note: Always uses hybrid recommendations (combines Collaborative Filtering + Content-Based)
    
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
        
        # Get recommendations using hybrid system (CF + Content-Based)
        # Accept hybrid parameters from request (optional)
        try:
            cf_weight = float(data.get('cf_weight', 0.7))  # Default: 70% CF, 30% CB
            cb_weight = float(data.get('cb_weight', 0.3))
            hybrid_method = str(data.get('hybrid_method', 'weighted'))
            # Validate hybrid_method
            if hybrid_method not in ['weighted', 'mixed', 'switching']:
                hybrid_method = 'weighted'
        except (ValueError, TypeError):
            # Use defaults if invalid values provided
            cf_weight = 0.7
            cb_weight = 0.3
            hybrid_method = 'weighted'
        
        recommendations, is_cold_start = get_recommendations(
            user_id=int(user_id),
            top_n=int(top_n),
            genre=genre,
            ratings_path=os.path.join(DATASET_PATH, 'ratings.csv'),
            movies_path=os.path.join(DATASET_PATH, 'movies.csv'),
            max_users=MAX_USERS,
            max_movies=MAX_MOVIES,
            download_images=True,
            image_dir='movie_posters',
            cf_weight=cf_weight,
            cb_weight=cb_weight,
            hybrid_method=hybrid_method
        )
        
        if not recommendations:
            # This should rarely happen now (cold start fallback should always return something)
            # But if it does, it's likely due to very restrictive genre filter
            error_msg = f'Error: No recommendations found for User ID {user_id}. Try removing genre filter or using a different User ID.'
            return jsonify({
                'success': False,
                'message': error_msg,
                'recommendations': [],
                'is_cold_start': False
            }), 200
        
        # Prepare response
        response_data = {
            'success': True,
            'recommendations': recommendations,
            'is_cold_start': is_cold_start,
            'recommendation_mode': 'hybrid'  # Always uses hybrid (CF + Content-Based)
        }
        
        # Add cold start message if applicable
        if is_cold_start:
            response_data['cold_start_message'] = f'No similar users found for user {user_id}. Using popular movies fallback (cold start solution).'
        
        return jsonify(response_data), 200
        
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

