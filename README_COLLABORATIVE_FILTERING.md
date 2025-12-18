# User-Based Collaborative Filtering - Technical Cheat Sheet

## ⚠️ IMPORTANT: This is USER-BASED CF (Not Item-Based)

**Type**: **User-Based Collaborative Filtering (UBCF)**
- Finds **similar users** → Uses their preferences → Recommends movies
- **NOT** Item-Based CF (which finds similar movies)

**Key Difference**:
- **User-Based**: "Users like you also liked..."
- **Item-Based**: "Movies similar to what you liked..."

---

## Quick Reference

| Aspect | Implementation |
|--------|---------------|
| **Algorithm Type** | User-Based Collaborative Filtering |
| **Similarity Metric** | Pearson Correlation Coefficient |
| **Prediction Method** | Weighted Average of Similar Users' Ratings |
| **Complexity** | O(u² × m) where u=users, m=movies |
| **Min Common Movies** | 5 (configurable) |
| **Top-K Similar Users** | 50 (configurable) |

---

## Overview

This document is a **technical cheat sheet** for the User-Based Collaborative Filtering implementation in MovieRec. It provides:
- Quick implementation reference
- Function signatures and purposes
- Design rationale
- Testing methods

---

## What is User-Based Collaborative Filtering?

**User-Based CF** is a recommendation technique that:

1. **Finds similar users** based on their rating patterns
2. **Uses similar users' preferences** to predict what the target user might like
3. **Recommends items** (movies) that similar users liked, but the target user hasn't rated

### Core Principle

> "Users who have similar tastes in the past will have similar tastes in the future."

**Example**: If User A and User B both liked movies X, Y, and Z, and User A also liked movie W, then User B will likely enjoy movie W too.

---

## Algorithm Flow

```
1. Load user ratings data
   ↓
2. Create user-movie rating matrix
   ↓
3. Find similar users (Pearson Correlation)
   ↓
4. Predict ratings for unrated movies
   ↓
5. Rank and return top-N recommendations
```

---

## Major Functions Explained

### 1. `pearson_correlation()` - Similarity Computation

**Location**: `backend/recommender/similarity.py`

**Purpose**: Calculates how similar two users are based on their rating patterns.

**How it works**:

1. Finds movies that **both users have rated**
2. Calculates Pearson Correlation Coefficient between their ratings
3. Returns a value between -1 and 1:
   - **+1**: Perfect positive correlation (same taste)
   - **0**: No correlation (different tastes)
   - **-1**: Perfect negative correlation (opposite tastes)

**Mathematical Formula**:

```
r = Σ((x_i - x̄)(y_i - ȳ)) / √(Σ(x_i - x̄)² × Σ(y_i - ȳ)²)
```

Where:
- `x_i`, `y_i`: Ratings from user 1 and user 2 for movie i
- `x̄`, `ȳ`: Average ratings of user 1 and user 2

**Why Pearson Correlation?**

- **Normalizes for rating bias**: Some users rate higher/lower on average
- **Measures linear relationship**: Captures how ratings change together
- **Well-established metric**: Widely used in recommender systems research
- **Interpretable**: Easy to understand and explain

**Example**:

```
User A ratings: [5, 4, 3, 5, 4]  (average: 4.2)
User B ratings: [4, 3, 2, 4, 3]  (average: 3.2)

Both users rate movies similarly (A always 1 point higher)
→ High positive correlation (~0.9)
→ Users are similar!
```

### 2. `find_similar_users()` - Finding Neighbors

**Location**: `backend/recommender/similarity.py`

**Signature**: `find_similar_users(target_user_id: int, user_movie_matrix: pd.DataFrame, min_common_movies: int = 5) -> List[Tuple[int, float]]`

**Purpose**: Identifies users most similar to the target user.

**Algorithm**:
1. For each user in dataset:
   - Calculate Pearson correlation with target
   - Require ≥ `min_common_movies` common ratings
   - Keep only positive correlations (similar, not opposite)
2. Sort by similarity (highest first)
3. Return `[(user_id, similarity_score), ...]`

**Parameters**:
- `min_common_movies=5`: Minimum shared movies
  - **Why?** Need enough data for reliable correlation
  - **Trade-off**: Higher = more reliable but fewer similar users

**Complexity**: O(u² × m) where u=users, m=movies per user

**Optimization Note**: For production, consider ANN algorithms

### 3. `predict_rating()` - Rating Prediction

**Location**: `backend/recommender/prediction.py`

**Signature**: `predict_rating(target_user_id: int, movie_id: int, user_movie_matrix: pd.DataFrame, similar_users: List[Tuple[int, float]], top_k: int = 50) -> float`

**Purpose**: Predicts how much the target user would rate a movie they haven't seen.

**Formula** (Weighted Average):
```
predicted = Σ(similarity_i × rating_i) / Σ|similarity_i|
```

**Why Weighted Average?**
- More similar users → more influence
- Normalizes by sum of similarities (handles varying number of raters)

**Example**:
```
Movie: "The Matrix"
Similar users:
  - User A (sim=0.9) rated: 5.0
  - User B (sim=0.7) rated: 4.0
  - User C (sim=0.5) rated: 3.0

Prediction = (0.9×5.0 + 0.7×4.0 + 0.5×3.0) / (0.9 + 0.7 + 0.5)
           = 8.8 / 2.1 = 4.19
```

### 4. `generate_recommendations()` - Main CF Algorithm

**Location**: `backend/recommender/collaborative_filtering.py`

**Signature**: `generate_recommendations(target_user_id: int, user_movie_matrix: pd.DataFrame, movies: pd.DataFrame, top_n: int = 4, genre_filter: str = None, min_common_movies: int = 5, top_k_similar: int = 50) -> List[Tuple[int, str, float, str, List[int]]]`

**Purpose**: Orchestrates the entire recommendation process.

**Algorithm Steps**:
1. Validate user exists
2. Get rated movies → exclude from recommendations
3. Find similar users (`find_similar_users()`)
4. Predict ratings for unrated movies (`predict_rating()`)
5. **Get similar users who rated each movie** (`get_similar_users_who_rated()`)
6. **Apply genre filter AFTER prediction** (if specified)
7. Sort by predicted rating (highest first)
8. Return top-N as `[(movie_id, title, rating, genres, similar_user_ids), ...]`

**New Feature**: Returns similar user IDs who rated each recommended movie (for display in modal)

**Genre Filtering**:
```python
# Applied AFTER prediction (not before)
if genre_filter and genre_filter.lower() not in movie_genres.lower():
    continue  # Skip
```

**Why Filter After Prediction?**
- ✅ Recommendations based on **user preferences** first
- ✅ Genre = **preference filter**, not hard constraint
- ✅ Maintains recommendation quality

---

## Why This CF Approach?

### Strengths

1. **Simple and Interpretable**
   - Easy to understand and explain
   - No "black box" - can trace why a movie was recommended

2. **No Training Required**
   - Works directly with user ratings
   - No model training phase needed

3. **Handles Cold Start for Items**
   - Can recommend new movies if similar users rated them
   - Doesn't need movie content features

4. **Captures User Preferences**
   - Learns from actual user behavior
   - Adapts to different user tastes

### Limitations

1. **Cold Start for Users**
   - New users with few ratings get poor recommendations
   - Need sufficient rating history

2. **Scalability Issues**
   - O(n²) complexity for similarity computation
   - Becomes slow with many users

3. **Sparsity Problem**
   - Most users haven't rated most movies
   - Hard to find common ratings

4. **Popularity Bias**
   - Tends to recommend popular movies
   - May miss niche recommendations

### Why Suitable for Academic Project?

1. **Educational Value**
   - Demonstrates core CF concepts clearly
   - Easy to explain in presentations
   - Well-documented algorithm

2. **Implementation Simplicity**
   - No complex machine learning libraries needed
   - Can be implemented from scratch
   - Easy to modify and experiment

3. **Baseline Performance**
   - Provides reasonable recommendations
   - Good starting point for comparison
   - Can be extended with improvements

---

## Algorithm Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Load data | O(n) | n = number of ratings |
| Create matrix | O(n) | Pivot table creation |
| Find similar users | O(u² × m) | u = users, m = movies per user |
| Predict ratings | O(k × m) | k = similar users, m = unrated movies |
| **Total** | **O(u² × m)** | Dominated by similarity computation |

**For 2000 users, 2000 movies**: ~4 billion operations (but optimized with early stopping)

---

## Extensions and Improvements

### Possible Enhancements

1. **Item-Based CF**: Similarity between movies instead of users
2. **Matrix Factorization**: SVD, NMF for dimensionality reduction
3. **Hybrid Approaches**: Combine CF with content-based filtering
4. **Deep Learning**: Neural collaborative filtering
5. **Real-time Updates**: Incremental similarity updates

### For Production

1. **Caching**: Cache similarity scores and recommendations
2. **Approximate Algorithms**: Use LSH or ANN for faster similarity
3. **Distributed Computing**: Parallelize similarity computation
4. **Database**: Replace CSV with proper database
5. **API Optimization**: Batch processing, async operations

---

## References

- **Resnick et al. (1994)**: "GroupLens: An Open Architecture for Collaborative Filtering"
- **Herlocker et al. (2004)**: "Evaluating Collaborative Filtering Recommender Systems"
- **Ricci et al. (2011)**: "Recommender Systems Handbook"

---

## Summary

This implementation of User-Based Collaborative Filtering provides:

- **Clear separation** of concerns (similarity, prediction, filtering)
- **Well-documented** functions with explanations
- **Academic correctness** following established CF principles
- **Practical usability** for real recommendation scenarios

The system is designed to be **understandable**, **explainable**, and **suitable for academic presentation** while maintaining correctness and functionality.

