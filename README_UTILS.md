# Utility Modules - Brief Documentation

## Overview

The `backend/utils/` package contains utility functions that support the recommender system but are separate from the core Collaborative Filtering logic.

---

## Modules

### 1. `image_downloader.py`

**Purpose**: Downloads movie poster images on-demand from TMDB API.

**Key Functions**:
- `download_movie_image()`: Download a single movie poster (resized to 270x400)
- `download_poster()`: Download and resize poster image from TMDB
- `image_exists()`: Check if image already exists locally
- `download_movie_images_batch()`: Download multiple images
- `ensure_movie_images()`: Ensure images exist for recommendations

**Usage**:
```python
from backend.utils import download_movie_image

# Download image if missing
image_path = download_movie_image("The Shawshank Redemption (1994)")
```

**Features**:
- Automatic filename sanitization (removes invalid characters like `:`)
- Checks for existing images to avoid re-downloading
- **Automatic image resizing**: All downloaded images are resized to 270x400 pixels (width x height) using Pillow
- Saves images to `movie_posters/` directory by default

---

### 2. `api_client.py`

**Purpose**: Handles external API calls to The Movie Database (TMDB).

**Key Functions**:
- `search_movie_tmdb()`: Search for movie on TMDB
- `get_movie_overview()`: Get movie description/overview
- `get_movie_poster_url()`: Get full URL for poster image

**Usage**:
```python
from backend.utils import get_movie_overview

# Get movie description
overview = get_movie_overview("The Matrix (1999)")
```

**Features**:
- Built-in API key (no setup required)
- Error handling for API failures
- Returns structured movie data

---

## Design Rationale

These utilities are **separated** from the core CF logic because:

1. **Separation of Concerns**: Image/API logic doesn't affect recommendation quality
2. **Modularity**: Can be replaced or updated independently
3. **Testability**: Easier to test utilities separately
4. **Clarity**: Core CF code remains focused on recommendation algorithm

---

## Dependencies

- `requests`: HTTP library for API calls
- `Pillow`: Image processing and resizing
- `os`, `re`: File system and string operations

---

## Notes

- Images are cached locally to reduce API calls
- API credentials are hardcoded for convenience (academic project)
- For production, use environment variables or config files

