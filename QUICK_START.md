# Quick Start Guide - MovieRec

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install pandas numpy requests
   ```

2. **Verify dataset is in place**:
   - Ensure `dataset/ratings.csv` and `dataset/movies.csv` exist

## Basic Usage

### Get Recommendations (Command Line)

```bash
python backend/main.py --user 189614 --top-n 4
```

### Get Recommendations with Genre Filter

```bash
python backend/main.py --user 189614 --top-n 4 --genre Action
```

### Use in Python Code

```python
from backend.main import get_recommendations

# Get 4 recommendations for user 189614 (Hybrid: CF + Content-Based)
recommendations = get_recommendations(
    user_id=189614,
    top_n=4,
    genre=None  # or "Action", "Comedy", etc.
)
# Uses hybrid system: 70% Collaborative Filtering + 30% Content-Based

# Customize hybrid weights
recommendations = get_recommendations(
    user_id=189614,
    top_n=4,
    cf_weight=0.8,  # 80% Collaborative Filtering
    cb_weight=0.2   # 20% Content-Based
)

# Each recommendation contains:
# - movie_id
# - title
# - predicted_rating
# - genres
# - image_path (if downloaded)
# - overview (from TMDB)
# - release_year
```

## Frontend Integration

The `index.html` file is ready for integration. Connect it to the backend API:

```javascript
// Example: Call backend API
fetch('/api/recommendations', {
    method: 'POST',
    body: JSON.stringify({
        user_id: 189614,
        top_n: 4,
        genre: 'Action'
    })
})
.then(response => response.json())
.then(recommendations => {
    // Display recommendations
    displayRecommendations(recommendations);
});
```

## Project Structure

- **Backend**: `backend/` directory
- **Frontend**: `index.html`
- **Data**: `dataset/` directory
- **Images**: `movie_posters/` directory (auto-created)

## Documentation

- **Main Project**: See `README_PROJECT.md`
- **CF Technical**: See `README_COLLABORATIVE_FILTERING.md`
- **Hybrid System**: See `README_HYBRID.md`
- **Utilities**: See `README_UTILS.md`
- **Structure**: See `STRUCTURE.md`

