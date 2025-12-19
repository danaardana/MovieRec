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

# Get 4 recommendations for user 189614
recommendations = get_recommendations(
    user_id=189614,
    top_n=4,
    genre=None  # or "Action", "Comedy", etc.
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

## Evaluate System Performance

### Quick Evaluation (Recommended)

```bash
# Fast evaluation on 100 users
python evaluate_system.py --sample-users 100 --top-n 10
```

### Evaluation with Custom Settings

```bash
# Evaluate on 50 users with top-5 recommendations
python evaluate_system.py --sample-users 50 --top-n 5

# Skip diversity calculation for even faster evaluation
python evaluate_system.py --sample-users 100 --skip-diversity
```

### View Results

Results are saved to `evaluation_results/` directory in multiple formats:
- `.json` - Structured data
- `.csv` - Tabular metrics
- `.log` - Detailed log
- `.txt` - Human-readable format

For more details, see **README_EVALUATION.md** or **QUICK_START_EVALUATION.md**.

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
- **Evaluation**: See `README_EVALUATION.md` and `QUICK_START_EVALUATION.md`
- **Utilities**: See `README_UTILS.md`
- **Structure**: See `STRUCTURE.md`

