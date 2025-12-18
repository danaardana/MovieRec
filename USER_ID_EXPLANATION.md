# Why Only Certain User IDs Are Available

## The Problem

When you try to use User IDs like 1, 2, 3, etc., you might get "User not found" errors. Only certain User IDs work (e.g., 149, 305, 461, 487, 897, 1109, 1595, 1677, 2012, 2172).

## Why This Happens

The system uses **filtering by user activity**, not by User ID number.

### How Data Filtering Works

1. **Loads all ratings** from the dataset
2. **Counts ratings per user** (how many movies each user rated)
3. **Selects top N most active users** (default: top 2000)
4. **Only these users are included** in the recommendation system

### Example

```
User ID 1: Rated 5 movies    → NOT in top 2000
User ID 149: Rated 500 movies → IN top 2000 ✓
User ID 305: Rated 450 movies → IN top 2000 ✓
```

**Result**: User IDs 1, 2, 3 might not be available, but 149, 305, etc. are.

## Why Filter by Activity?

1. **Memory Efficiency**: Large datasets can't fit in memory
2. **Better Recommendations**: Active users have more data for similarity calculation
3. **Performance**: Fewer users = faster similarity computation

## Current Limitations

- **Form accepts**: User IDs 1-99 (for simplicity)
- **Actually available**: Only users in top 2000 most active
- **Mismatch**: Low-numbered User IDs (1-99) may not be in top active users

## Solutions

### Option 1: Use Available User IDs
Try User IDs that are actually in the filtered dataset:
- 149, 305, 461, 487, 897, 1109, 1595, 1677, 2012, 2172, etc.

### Option 2: Increase max_users
In `app.py`, change:
```python
MAX_USERS = 2000  # Increase to 5000 or more
```

### Option 3: Filter by User ID Range Instead
Modify `backend/data_loader.py` to filter by User ID range (1-99) instead of activity:
```python
# Instead of filtering by activity
ratings = ratings[(ratings['userId'] >= 1) & (ratings['userId'] <= 99)]
```

## Current Form Validation

- **HTML5**: `min="1" max="99"` - Prevents input outside range
- **JavaScript**: Validates 1-99 before sending request
- **Backend**: Validates 1-99 and provides helpful error messages

## Recommendation

For academic projects, it's often better to:
1. **Keep activity-based filtering** (better recommendations)
2. **Show available User IDs** in the error message
3. **Or filter by User ID range** if you specifically need IDs 1-99

The current implementation prioritizes recommendation quality over User ID convenience.

