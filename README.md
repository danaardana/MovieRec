# MovieRec - Movie Recommendation System

> **Academic Project**: A simple User-Based Collaborative Filtering recommender system with web interface

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Features](#features)
- [Technologies](#technologies)

## Overview

MovieRec is an educational recommender system that demonstrates **User-Based Collaborative Filtering** for movie recommendations. It combines a Python backend with an HTML frontend to provide personalized movie recommendations.

**Key Characteristics**:
- ✅ User-Based Collaborative Filtering
- ✅ Pearson Correlation for similarity
- ✅ Explicit ratings-based recommendations
- ✅ Genre filtering support
- ✅ **Cold Start Solution**: Popular movies fallback for users with few ratings
- ✅ Automatic image downloading
- ✅ **Notification Bar**: Real-time feedback for cold start and errors
- ✅ Clean, modular code structure

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install pandas numpy requests flask flask-cors Pillow
```

### 2. Start Flask Server

```bash
python app.py
```

Then open browser: `http://localhost:5000`

**Or test backend directly**:
```bash
python backend/main.py --user 24 --top-n 4
```

### 3. Use in Code

```python
from backend.main import get_recommendations

recommendations = get_recommendations(
    user_id=24,  # Any positive user ID
    top_n=4,
    genre="Action"  # optional
)

# Each recommendation includes:
# - movie_id, title, predicted_rating, genres
# - image_path, overview, release_year
# - similar_user_ids (list of user IDs who contributed to the prediction)
```

## Project Structure

```
MovieRec/
├── backend/                    # Python backend
│   ├── recommender/            # CF algorithm modules
│   │   ├── collaborative_filtering.py
│   │   ├── similarity.py
│   │   └── prediction.py
│   ├── utils/                  # Utility modules
│   │   ├── image_downloader.py
│   │   └── api_client.py
│   ├── data_loader.py          # Data loading
│   └── main.py                 # Main API endpoint
├── dataset/                    # MovieLens dataset (excluded in .gitignore)
├── movie_posters/              # Downloaded images
├── index.html                  # Frontend interface
├── .gitignore                  # Git ignore rules
└── README files                # Documentation
```

## Documentation

| Document | Purpose |
|----------|---------|
| **README_PROJECT.md** | System architecture, integration guide, application flow |
| **README_COLLABORATIVE_FILTERING.md** | Technical CF documentation, algorithm explanation |
| **README_UTILS.md** | Utility modules documentation |
| **STRUCTURE.md** | Complete file structure overview |
| **QUICK_START.md** | Quick setup and usage guide |

## Features

### Core Recommendation System
- **User-Based Collaborative Filtering**: Finds similar users and recommends based on their preferences
- **Pearson Correlation**: Measures user similarity accurately
- **Genre Filtering**: Optional genre filter applied after recommendation
- **Top-N Recommendations**: Configurable number of recommendations

### Additional Features
- **Cold Start Solution**: Automatically falls back to popular movies when no similar users are found (solves cold start problem)
- **Notification Bar**: Non-intrusive notifications for cold start events and errors (auto-dismisses after 5-8 seconds)
- **Image Downloading**: Automatic poster image fetching from TMDB (270x400 for cards, 340x490 for modal)
- **Movie Metadata**: Overview and details from external API
- **Similar User IDs**: Shows which similar users rated each movie (in modal)
- **Error Handling**: User-friendly error modals for actual errors (cold start uses notification bar only, no modal)
- **User Inclusion**: Requested users are always included in dataset, even if not in top N most active users
- **Memory Efficient**: Handles large datasets efficiently
- **Modular Design**: Clean separation of concerns
- **No RuntimeWarnings**: Fixed numpy division warnings in correlation calculation

## Technologies

**Backend**:
- Python 3.x
- Pandas (data manipulation)
- NumPy (numerical computations)
- Requests (API calls)

**Frontend**:
- HTML5
- CSS3
- JavaScript

**External Services**:
- The Movie Database (TMDB) API

**Data**:
- MovieLens Dataset

## Frontend Integration

The `index.html` file contains the frontend interface with:

- **Banner Section**: Input form (User ID, Genre, Top-N)
- **Notification Bar**: Shows info/error notifications at the top (auto-dismisses after 5-8 seconds)
  - **Cold start**: Shows terminal-style message "Warning: No similar users found. Using popular movies fallback (cold start solution)." (info type, no error modal)
  - **Errors**: Shows error messages (error type, shows error modal for actual errors)
  - Manual close button available
  - Color-coded: purple (info), red (error), green (success), yellow (warning)
- **Work Section**: Displays recommendations when Top-N < 6 (1-5 recommendations, 270x400 card images)
- **Gallery Section**: Displays recommendations when Top-N ≥ 6 (6+ recommendations, 270x400 card images)
- **Modal Popup**: Detailed movie information including:
  - Movie poster (340x490)
  - Title, release year, predicted rating
  - All genres
  - **Similar User IDs** who rated this movie
  - **Overview** section with movie description

**Fully Integrated**: Form automatically connects to Flask API at `/api/recommendations`

**Cold Start Handling**: 
- When a user has few ratings (e.g., User ID 1 or 2), the system automatically shows popular movies instead of failing
- Shows notification bar only (no error modal) with terminal-style message
- All users are included in dataset even if not in top N most active users (prevents "user not found" errors)

## Academic Context

This project is designed for:
- **University courses** on Recommender Systems
- **Educational demonstrations** of Collaborative Filtering
- **Academic presentations** and reports

**Not intended for commercial use.**

## License

Academic/Educational use only. MovieLens data subject to GroupLens Research license.

---

**For detailed documentation, see the README files listed above.**
