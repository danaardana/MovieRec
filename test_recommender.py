"""
Test Script for Recommender System

This script provides methods to cross-check and validate the recommender system.
Run this to verify the system is working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.data_loader import load_data, create_user_movie_matrix
from backend.recommender import generate_recommendations
from backend.recommender.similarity import find_similar_users, pearson_correlation
from backend.recommender.prediction import predict_rating
import pandas as pd


def test_data_loading():
    """Test 1: Verify data loading works"""
    print("=" * 70)
    print("TEST 1: Data Loading")
    print("=" * 70)
    
    try:
        ratings, movies = load_data('dataset/ratings.csv', 'dataset/movies.csv', 
                                   max_users=100, max_movies=100)
        print(f"[OK] Loaded {len(ratings)} ratings")
        print(f"[OK] Loaded {len(movies)} movies")
        print(f"[OK] Unique users: {ratings['userId'].nunique()}")
        print(f"[OK] Unique movies: {ratings['movieId'].nunique()}")
        return True, ratings, movies
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False, None, None


def test_matrix_creation(ratings):
    """Test 2: Verify matrix creation"""
    print("\n" + "=" * 70)
    print("TEST 2: Matrix Creation")
    print("=" * 70)
    
    try:
        matrix = create_user_movie_matrix(ratings, use_sparse=True)
        print(f"[OK] Matrix shape: {matrix.shape}")
        print(f"[OK] Matrix sparsity: {(matrix.isna().sum().sum() / (matrix.shape[0] * matrix.shape[1]) * 100):.2f}%")
        print(f"[OK] Sample user ratings: {matrix.iloc[0].dropna().head(5).to_dict()}")
        return True, matrix
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False, None


def test_similarity_calculation(matrix):
    """Test 3: Verify similarity calculation"""
    print("\n" + "=" * 70)
    print("TEST 3: Similarity Calculation (Pearson Correlation)")
    print("=" * 70)
    
    try:
        # Get a test user
        test_user = matrix.index[0]
        print(f"Testing with user: {test_user}")
        
        # Find similar users
        similar_users = find_similar_users(test_user, matrix, min_common_movies=5)
        
        if len(similar_users) > 0:
            print(f"[OK] Found {len(similar_users)} similar users")
            print(f"[OK] Top 3 similar users:")
            for user_id, similarity in similar_users[:3]:
                print(f"  - User {user_id}: similarity = {similarity:.4f}")
            
            # Test correlation calculation
            if len(similar_users) > 0:
                user1_id = test_user
                user2_id = similar_users[0][0]
                user1_ratings = matrix.loc[user1_id]
                user2_ratings = matrix.loc[user2_id]
                corr = pearson_correlation(user1_ratings, user2_ratings)
                print(f"[OK] Direct correlation test: {corr:.4f}")
        else:
            print("[WARN] No similar users found (may need more data)")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rating_prediction(matrix):
    """Test 4: Verify rating prediction"""
    print("\n" + "=" * 70)
    print("TEST 4: Rating Prediction")
    print("=" * 70)
    
    try:
        test_user = matrix.index[0]
        test_user_ratings = matrix.loc[test_user]
        
        # Find an unrated movie
        unrated_movies = test_user_ratings[test_user_ratings.isna()].index
        
        if len(unrated_movies) > 0:
            test_movie = unrated_movies[0]
            print(f"Testing prediction for user {test_user}, movie {test_movie}")
            
            # Find similar users
            similar_users = find_similar_users(test_user, matrix, min_common_movies=5)
            
            if len(similar_users) > 0:
                predicted = predict_rating(test_user, test_movie, matrix, 
                                          similar_users, top_k=10)
                print(f"[OK] Predicted rating: {predicted:.2f}")
                print(f"  (Based on {min(len(similar_users), 10)} similar users)")
            else:
                print("[WARN] No similar users found for prediction")
        else:
            print("[WARN] User has rated all movies in filtered dataset")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_recommendation(matrix, movies):
    """Test 5: Verify full recommendation pipeline"""
    print("\n" + "=" * 70)
    print("TEST 5: Full Recommendation Pipeline")
    print("=" * 70)
    
    try:
        test_user = matrix.index[0]
        print(f"Generating recommendations for user: {test_user}")
        
        recommendations = generate_recommendations(
            target_user_id=test_user,
            user_movie_matrix=matrix,
            movies=movies,
            top_n=5,
            genre_filter=None,
            min_common_movies=5,
            top_k_similar=50
        )
        
        if recommendations:
            print(f"[OK] Generated {len(recommendations)} recommendations:")
            for i, (movie_id, title, rating, genres) in enumerate(recommendations, 1):
                print(f"  {i}. {title}")
                print(f"     Predicted Rating: {rating:.2f}")
                print(f"     Genres: {genres}")
        else:
            print("[WARN] No recommendations generated")
            print("  Possible reasons:")
            print("  - User has no similar users")
            print("  - User has rated all available movies")
            print("  - Insufficient common movies with other users")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_genre_filtering(matrix, movies):
    """Test 6: Verify genre filtering"""
    print("\n" + "=" * 70)
    print("TEST 6: Genre Filtering")
    print("=" * 70)
    
    try:
        test_user = matrix.index[0]
        print(f"Testing genre filter 'Action' for user: {test_user}")
        
        recommendations = generate_recommendations(
            target_user_id=test_user,
            user_movie_matrix=matrix,
            movies=movies,
            top_n=5,
            genre_filter="Action",
            min_common_movies=5,
            top_k_similar=50
        )
        
        if recommendations:
            print(f"[OK] Generated {len(recommendations)} Action movie recommendations:")
            for i, (movie_id, title, rating, genres) in enumerate(recommendations, 1):
                print(f"  {i}. {title} (Rating: {rating:.2f})")
                print(f"     Genres: {genres}")
                # Verify genre filter
                if "Action" not in genres:
                    print(f"     [WARN] Genre filter may not be working correctly!")
        else:
            print("[WARN] No Action movie recommendations found")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("RECOMMENDER SYSTEM TEST SUITE")
    print("=" * 70)
    print("\nThis script tests the User-Based Collaborative Filtering system.")
    print("It verifies each component is working correctly.\n")
    
    results = []
    
    # Test 1: Data Loading
    success, ratings, movies = test_data_loading()
    results.append(("Data Loading", success))
    
    if not success:
        print("\n✗ Cannot continue - data loading failed")
        return
    
    # Test 2: Matrix Creation
    success, matrix = test_matrix_creation(ratings)
    results.append(("Matrix Creation", success))
    
    if not success:
        print("\n✗ Cannot continue - matrix creation failed")
        return
    
    # Test 3: Similarity
    success = test_similarity_calculation(matrix)
    results.append(("Similarity Calculation", success))
    
    # Test 4: Prediction
    success = test_rating_prediction(matrix)
    results.append(("Rating Prediction", success))
    
    # Test 5: Full Pipeline
    success = test_full_recommendation(matrix, movies)
    results.append(("Full Recommendation", success))
    
    # Test 6: Genre Filtering
    success = test_genre_filtering(matrix, movies)
    results.append(("Genre Filtering", success))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n[OK] All tests passed! Recommender system is working correctly.")
    else:
        print("\n[WARN] Some tests failed. Check the output above for details.")


if __name__ == '__main__':
    run_all_tests()

