# Hybrid Recommendation System

This document explains how to use the hybrid recommendation system that combines Collaborative Filtering (CF) and Content-Based Filtering (CB).

## Overview

The hybrid system combines two recommendation approaches:

1. **Collaborative Filtering (CF)**: Recommends movies based on similar users' preferences
2. **Content-Based Filtering (CB)**: Recommends movies similar to what the user has liked based on genre similarity

## Hybrid Methods

### 1. Weighted Combination (Default)

Combines scores from both approaches using weighted average.

```python
from backend.main import get_recommendations

recommendations, is_cold_start = get_recommendations(
    user_id=24,
    top_n=10,
    use_hybrid=True,
    cf_weight=0.7,  # 70% weight for CF
    cb_weight=0.3,  # 30% weight for CB
    hybrid_method='weighted'
)
```

### 2. Mixed Combination

Takes top recommendations from both approaches and combines them.

```python
recommendations, is_cold_start = get_recommendations(
    user_id=24,
    top_n=10,
    use_hybrid=True,
    hybrid_method='mixed'
)
```

### 3. Switching

Uses CF if available, falls back to CB if no similar users found.

```python
recommendations, is_cold_start = get_recommendations(
    user_id=24,
    top_n=10,
    use_hybrid=True,
    hybrid_method='switching'
)
```

## Benefits of Hybrid Approach

1. **Better Coverage**: Handles both collaborative and content preferences
2. **Cold Start Improvement**: Content-based can work even with few similar users
3. **Serendipity**: Balances popular recommendations (CF) with diverse content (CB)
4. **Robustness**: Falls back gracefully when one approach fails

## Usage Examples

### Basic Hybrid (Weighted)

```python
from backend.main import get_recommendations

recommendations, is_cold_start = get_recommendations(
    user_id=24,
    top_n=10,
    use_hybrid=True
)
```

### Custom Weights

```python
# More weight to content-based (good for users with unique tastes)
recommendations, is_cold_start = get_recommendations(
    user_id=24,
    top_n=10,
    use_hybrid=True,
    cf_weight=0.5,
    cb_weight=0.5
)

# More weight to collaborative (good for users with common preferences)
recommendations, is_cold_start = get_recommendations(
    user_id=24,
    top_n=10,
    use_hybrid=True,
    cf_weight=0.8,
    cb_weight=0.2
)
```

### With Genre Filter

```python
recommendations, is_cold_start = get_recommendations(
    user_id=24,
    top_n=10,
    genre="Action",
    use_hybrid=True
)
```

## API Integration

### Flask/Backend

The hybrid mode can be enabled via API:

```python
# In app.py or your API endpoint
recommendations, is_cold_start = get_recommendations(
    user_id=int(request.json['user_id']),
    top_n=int(request.json.get('top_n', 4)),
    genre=request.json.get('genre'),
    use_hybrid=request.json.get('use_hybrid', False),
    cf_weight=request.json.get('cf_weight', 0.7),
    cb_weight=request.json.get('cb_weight', 0.3)
)
```

## How It Works

### Content-Based Component

1. **Builds User Profile**: Analyzes genres of movies the user rated highly (≥3.5)
2. **Calculates Similarity**: Uses cosine similarity between movie genres and user profile
3. **Recommends**: Suggests movies with similar genre profiles

### Hybrid Combination

- **Weighted**: Combines normalized scores: `score = cf_score * cf_weight + cb_score * cb_weight`
- **Mixed**: Takes top-N from each approach, deduplicates, combines scores
- **Switching**: Uses CF when available, CB as fallback

## Performance Considerations

- Hybrid is slightly slower than pure CF (requires both approaches)
- Content-based filtering adds minimal overhead (genre parsing is fast)
- Weighted method is most computationally efficient
- Mixed method provides best diversity but takes longer

## When to Use Hybrid

**Use Hybrid When:**
- You want better recommendation diversity
- Users have unique preferences (not well-covered by similar users)
- You want to improve cold start handling
- You want to balance popularity (CF) with content similarity (CB)

**Use Pure CF When:**
- Performance is critical
- Users have many similar users
- Collaborative signals are strong
- Simple, fast recommendations are priority

## Configuration Recommendations

| Scenario | CF Weight | CB Weight | Method |
|----------|-----------|-----------|--------|
| Default | 0.7 | 0.3 | weighted |
| Content-focused | 0.5 | 0.5 | weighted |
| CF-focused | 0.8 | 0.2 | weighted |
| Maximum diversity | 0.6 | 0.4 | mixed |
| Cold start handling | - | - | switching |
