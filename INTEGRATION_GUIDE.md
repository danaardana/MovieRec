# Frontend-Backend Integration Guide

## Quick Start

### 1. Start the Flask Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### 2. Open the Frontend

Open your browser and navigate to:
```
http://localhost:5000/
```

### 3. Use the Application

1. Enter a **User ID** (e.g., 189614)
2. Optionally select a **Movie Category** (genre filter)
3. Enter **Number of Recommendations** (default: 4)
4. Click **"Get Recommendations"**

## How It Works

### Frontend (index.html)

1. **Form Submission**: When user submits the form, JavaScript intercepts it
2. **API Call**: Sends POST request to `/api/recommendations` with:
   - `user_id`: User ID from form
   - `top_n`: Number of recommendations
   - `category`: Selected genre (optional)

3. **Display Logic**:
   - If `top_n <= 4`: Displays in **Work Section** (swiper carousel)
   - If `top_n > 4`: Displays in **Gallery Section** (grid layout)

4. **Modal Popup**: Clicking a movie card opens a modal with:
   - Movie poster
   - Title
   - Release year
   - All genres
   - Movie overview/description

### Backend (app.py)

1. **Receives Request**: Flask endpoint `/api/recommendations` receives POST request
2. **Calls Backend**: Uses `backend.main.get_recommendations()` function
3. **Processes Data**:
   - Loads dataset
   - Generates recommendations using Collaborative Filtering
   - Downloads missing poster images
   - Fetches movie overviews from TMDB API
4. **Returns JSON**: Sends formatted recommendations back to frontend

## API Endpoints

### POST /api/recommendations

**Request Body**:
```json
{
    "user_id": 189614,
    "top_n": 4,
    "category": "Action"  // optional
}
```

**Response**:
```json
{
    "success": true,
    "recommendations": [
        {
            "movie_id": 208703,
            "title": "1917 (2019)",
            "predicted_rating": 4.08,
            "genres": "Action|Drama|War",
            "image_path": "movie_posters/1917_(2019).jpg",
            "overview": "Movie description...",
            "release_year": "2019"
        },
        ...
    ]
}
```

### GET /movie_posters/<filename>

Serves movie poster images from the `movie_posters/` directory.

## Data Flow

```
User Input (Form)
    ↓
JavaScript (index.html)
    ↓
POST /api/recommendations
    ↓
Flask Server (app.py)
    ↓
Backend Main (backend/main.py)
    ↓
├── Data Loader (loads CSV files)
├── Collaborative Filtering (generates recommendations)
├── Image Downloader (fetches posters)
└── API Client (fetches overviews)
    ↓
JSON Response
    ↓
JavaScript (displays recommendations)
    ↓
User sees recommendations
```

## Troubleshooting

### Server Not Starting

**Error**: `ModuleNotFoundError: No module named 'flask'`
**Solution**: Install Flask: `pip install flask flask-cors`

### No Recommendations Found

**Possible Causes**:
1. User ID not in filtered dataset (try increasing `MAX_USERS` in `app.py`)
2. User has no similar users
3. Genre filter too restrictive

**Solution**: Try a different User ID (e.g., 189614, 48766, 207216)

### Images Not Loading

**Possible Causes**:
1. Images not downloaded yet (first request may take time)
2. TMDB API rate limit
3. Image path incorrect

**Solution**: Check `movie_posters/` directory, images should be downloaded automatically

### CORS Errors

**Error**: `Access-Control-Allow-Origin` error
**Solution**: Flask-CORS is already enabled in `app.py`, should work automatically

## Testing the Integration

### Test API Directly

```bash
curl -X POST http://localhost:5000/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{"user_id": 189614, "top_n": 4}'
```

### Test in Browser

1. Start server: `python app.py`
2. Open browser: `http://localhost:5000`
3. Open Developer Tools (F12)
4. Go to Network tab
5. Submit form and check API request/response

## Production Considerations

For production deployment:

1. **Use Production WSGI Server**: Use Gunicorn or uWSGI instead of Flask dev server
2. **Environment Variables**: Move API keys to environment variables
3. **Error Handling**: Add more robust error handling
4. **Caching**: Cache recommendations and images
5. **Database**: Replace CSV files with proper database
6. **HTTPS**: Use HTTPS for security
7. **Rate Limiting**: Add rate limiting to prevent abuse

## File Structure

```
MovieRec/
├── app.py                    # Flask API server
├── index.html                # Frontend (with integrated JS)
├── backend/
│   ├── main.py              # Main recommendation function
│   ├── recommender/         # CF algorithm
│   ├── utils/               # Image downloader, API client
│   └── data_loader.py       # Data loading
├── dataset/                 # MovieLens data
└── movie_posters/           # Downloaded images
```

## Next Steps

1. **Test the integration**: Start server and test in browser
2. **Customize styling**: Adjust CSS if needed
3. **Add features**: Enhance modal, add filters, etc.
4. **Deploy**: Deploy to production server if needed

