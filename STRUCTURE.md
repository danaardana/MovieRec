# Project Structure Overview

## Complete File Structure

```
MovieRec/
├── backend/
│   ├── recommender/
│   │   ├── __init__.py                    # Package exports
│   │   ├── collaborative_filtering.py     # Main CF algorithm
│   │   ├── similarity.py                  # Pearson correlation
│   │   └── prediction.py                   # Rating prediction
│   ├── utils/
│   │   ├── __init__.py                    # Package exports
│   │   ├── image_downloader.py            # Image downloading
│   │   └── api_client.py                  # TMDB API client
│   ├── data_loader.py                     # Data loading & preprocessing
│   └── main.py                            # Main API endpoint
├── dataset/
│   ├── ratings.csv
│   ├── movies.csv
│   └── README.txt
├── movie_posters/                          # Downloaded images
├── index.html                              # Frontend interface
├── README_PROJECT.md                       # Main project documentation
├── README_COLLABORATIVE_FILTERING.md       # Technical CF documentation
├── README_UTILS.md                         # Utility modules documentation
└── requirements.txt                        # Python dependencies
```

## Module Responsibilities

### Core Recommendation Logic
- **`backend/recommender/collaborative_filtering.py`**: Main algorithm orchestrator
- **`backend/recommender/similarity.py`**: User similarity computation
- **`backend/recommender/prediction.py`**: Rating prediction logic

### Data Management
- **`backend/data_loader.py`**: Loads and preprocesses CSV data

### Utilities
- **`backend/utils/image_downloader.py`**: Downloads movie posters
- **`backend/utils/api_client.py`**: Handles TMDB API calls

### Integration
- **`backend/main.py`**: Main entry point, formats data for frontend

## Import Structure

```python
# Main entry point
from backend.main import get_recommendations

# Core CF components
from backend.recommender import generate_recommendations
from backend.recommender.similarity import find_similar_users
from backend.recommender.prediction import predict_rating

# Data loading
from backend.data_loader import load_data, create_user_movie_matrix

# Utilities
from backend.utils import download_movie_image, get_movie_overview
```

