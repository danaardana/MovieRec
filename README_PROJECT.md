# MovieRec - Movie Recommendation System

## Project Overview

MovieRec is a simple academic movie recommendation system built as part of a university project. It demonstrates User-Based Collaborative Filtering integrated with a web-based frontend interface.

**Project Type:** Educational/Academic Prototype  
**Purpose:** Demonstrate core recommender system concepts  
**Status:** Non-commercial, educational use only

---

## System Architecture

### High-Level Architecture

```
┌─────────────────┐
│   Frontend      │
│   (index.html)  │
└────────┬────────┘
         │ HTTP Request
         │ (User ID, Genre, Top-N)
         ▼
┌─────────────────┐
│   Backend API   │
│  (backend/main) │
└────────┬────────┘
         │
         ├──► Data Loader
         │    (Load ratings & movies)
         │
         ├──► Collaborative Filtering
         │    (Generate recommendations)
         │
         └──► Image Downloader
              (Fetch movie posters)
```

### Directory Structure

```
MovieRec/
├── backend/
│   ├── recommender/
│   │   ├── __init__.py
│   │   ├── collaborative_filtering.py  # Main CF logic
│   │   ├── similarity.py                # Pearson correlation
│   │   └── prediction.py                # Rating prediction
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── image_downloader.py          # Image fetching
│   │   └── api_client.py                # TMDB API client
│   ├── data_loader.py                   # Data loading & preprocessing
│   └── main.py                           # Main API endpoint
├── dataset/
│   ├── ratings.csv
│   ├── movies.csv
│   └── README.txt
├── movie_posters/                        # Downloaded images
├── index.html                            # Frontend interface
├── .gitignore                           # Git ignore rules (excludes dataset/)
└── README_PROJECT.md                     # This file
```

---

## Application Flow

### 1. User Input (Frontend)

The user interacts with the form in the **Banner Section** of `index.html`:

- **User ID** (required): Identifies the user for personalized recommendations
- **Movie Genre** (optional): Filters recommendations by genre
- **Top-N Recommendations** (optional, default: 4): Number of movies to recommend

### 2. Backend Processing

When a request is received:

1. **Data Loading** (`data_loader.py`)
   - Loads ratings and movie data from CSV files
   - Creates user-movie rating matrix
   - Filters data for memory efficiency (if needed)

2. **Collaborative Filtering** (`recommender/collaborative_filtering.py`)
   - Finds similar users using Pearson Correlation
   - Predicts ratings for unrated movies
   - Generates ranked recommendation list
   - Applies genre filter (if specified) **after** prediction

3. **Image Downloading** (`utils/image_downloader.py`)
   - Checks if poster images exist locally
   - Downloads missing images from TMDB API
   - Resizes images to 270x400 pixels (width x height) for cards
   - Saves images with sanitized filenames

4. **Metadata Fetching** (`utils/api_client.py`)
   - Retrieves movie overview/description from TMDB
   - Gets additional movie metadata

### 3. Response Format

The backend returns a JSON array of recommendations:

```json
[
  {
    "movie_id": 123,
    "title": "The Shawshank Redemption (1994)",
    "predicted_rating": 4.5,
    "genres": "Drama|Crime",
    "image_path": "movie_posters/The_Shawshank_Redemption_(1994).jpg",
    "overview": "Two imprisoned men bond over a number of years...",
    "release_year": "1994",
    "similar_user_ids": [189614, 48766, 207216]
  },
  ...
]
```

### 4. Frontend Display

- **Work Section**: Displays Top-4 recommendations (when Top-N = 4) with 270x400 card images
- **Gallery Section**: Displays more than 4 recommendations (when Top-N > 4) with 270x400 card images
- **Modal Popup**: Shows detailed movie information when a card is clicked:
  - Movie poster (340x490)
  - Title, release year, predicted rating
  - All genres
  - Similar User IDs who rated this movie
  - **Overview** section with movie description

---

## Technologies Used

### Backend
- **Python 3.x**: Core programming language
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computations
- **Requests**: HTTP library for API calls

### Frontend
- **HTML5**: Structure
- **CSS3**: Styling
- **JavaScript**: Interactivity and API calls

### External APIs
- **The Movie Database (TMDB)**: Movie metadata and poster images

### Data Source
- **MovieLens Dataset**: User ratings and movie information

---

## Integration Guide

### Backend Setup

1. **Install Dependencies**:
   ```bash
   pip install pandas numpy requests
   ```

2. **Run Backend** (for testing):
   ```bash
   python backend/main.py --user 189614 --top-n 4
   ```

### Frontend Integration

The frontend (`index.html`) should make HTTP requests to the backend API.

**Example Integration** (using Fetch API):

```javascript
async function getRecommendations(userId, genre, topN) {
    const response = await fetch('/api/recommendations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            user_id: userId,
            genre: genre,
            top_n: topN
        })
    });
    
    const recommendations = await response.json();
    return recommendations;
}
```

**Backend API Endpoint** (to be implemented with Flask/FastAPI):

```python
from backend.main import get_recommendations

@app.route('/api/recommendations', methods=['POST'])
def recommendations():
    data = request.json
    results = get_recommendations(
        user_id=data['user_id'],
        top_n=data.get('top_n', 4),
        genre=data.get('genre')
    )
    return jsonify(results)
```

---

## Key Design Decisions

### 1. Genre Filtering After Prediction

**Decision**: Genre filter is applied **after** generating recommendations, not during similarity computation.

**Rationale**:
- Recommendations are based purely on user preferences
- Genre acts as a post-filter, not a constraint
- Maintains recommendation quality while allowing genre preferences

### 2. Memory-Efficient Matrix Creation

**Decision**: Uses sparse matrix representation for large datasets.

**Rationale**:
- MovieLens dataset is very large (33M+ ratings)
- Full dense matrix would require 200+ GB RAM
- Sparse representation reduces memory to ~30 MB for 2000x2000 matrix

### 3. Separate Utility Modules

**Decision**: Image downloading and API calls are separated from core CF logic.

**Rationale**:
- Clear separation of concerns
- Easier to test and maintain
- Can be replaced/swapped without affecting CF algorithm

---

## File Responsibilities

| File | Responsibility |
|------|---------------|
| `backend/main.py` | Main API endpoint, orchestrates all components |
| `backend/data_loader.py` | Loads and preprocesses data |
| `backend/recommender/collaborative_filtering.py` | Main CF algorithm implementation |
| `backend/recommender/similarity.py` | User similarity computation (Pearson) |
| `backend/recommender/prediction.py` | Rating prediction from similar users |
| `backend/utils/image_downloader.py` | Downloads movie poster images |
| `backend/utils/api_client.py` | Handles TMDB API calls |

---

## Future Enhancements

For production use, consider:

1. **Web Framework Integration**: Flask or FastAPI for REST API
2. **Database**: Replace CSV files with proper database
3. **Caching**: Cache recommendations and images
4. **Performance**: Optimize similarity computation (e.g., use sparse matrices)
5. **Error Handling**: More robust error handling and validation
6. **Authentication**: User authentication system
7. **Logging**: Comprehensive logging system

---

## Academic Context

This project demonstrates:

- **Collaborative Filtering**: User-based recommendation approach
- **Similarity Metrics**: Pearson Correlation for user similarity
- **Data Preprocessing**: Handling large-scale datasets
- **System Integration**: Frontend-backend integration
- **API Integration**: External API usage for metadata

**Suitable for**: University courses on Recommender Systems, Machine Learning, or Web Development.

---

## License & Usage

This is an **academic, non-commercial project**. The MovieLens dataset is provided by GroupLens Research and is subject to their license terms.

**For Educational Use Only**

