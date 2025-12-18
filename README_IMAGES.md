# Download Movie Images

This guide explains how to download movie poster images for the top movies.

## Quick Start

**The API key is already built into the program!** You can start downloading images right away:

```bash
python download_movie_images.py --top-n 10
```

That's it! No API key needed - everything is already configured.

## Usage Examples

**Download top 10 movie posters:**
```bash
python download_movie_images.py --top-n 10
```

**Download top 20 highest-rated movies (min 100 ratings):**
```bash
python download_movie_images.py --top-n 20 --min-ratings 100
```

**Download most popular movies:**
```bash
python download_movie_images.py --top-n 15 --sort-by count
```

**Custom output directory:**
```bash
python download_movie_images.py --top-n 10 --output-dir my_posters
```

## API Key Information

**The API key is already built into the program**, so you don't need to provide it. However, if you want to use your own API key, you can:

**Option 1: Command line argument**
```bash
python download_movie_images.py --api-key YOUR_API_KEY --top-n 10
```

**Option 2: Environment variable**

**Windows (PowerShell):**
```powershell
$env:TMDB_API_KEY="your_api_key_here"
python download_movie_images.py --top-n 10
```

**Windows (Command Prompt):**
```cmd
set TMDB_API_KEY=your_api_key_here
python download_movie_images.py --top-n 10
```

**Linux/Mac:**
```bash
export TMDB_API_KEY="your_api_key_here"
python download_movie_images.py --top-n 10
```

**Note**: The built-in API key works for most use cases. You only need to provide your own if you want to use a different account or if the built-in key stops working.

## Output

Images are saved in the `movie_posters` directory (or your custom directory) with sanitized filenames:
- Invalid characters like `:` are replaced with `_`
- Example: `The Shawshank Redemption (1994).jpg`

## File Naming

The script automatically sanitizes filenames to be Windows-compatible:
- Removes invalid characters: `: < > " | ? * \`
- Replaces spaces and special chars with underscores
- Limits filename length to 200 characters

## Troubleshooting

**"Invalid API key"**
- The built-in API key should work automatically
- If you're using your own API key, double-check it's correct
- Make sure you've activated your TMDB account (if using your own key)
- Wait a few minutes after creating a new API key - it may take time to activate

**"Poster not found"**
- Some movies might not have posters on TMDB
- Try increasing `--min-ratings` to get more popular movies (which are more likely to have posters)

**Images not downloading**
- Check your internet connection
- TMDB API has rate limits - wait a few seconds between runs if you get errors

## Requirements

- `requests` library (install with `pip install requests`)
- Internet connection (to download images from TMDB)

**Note**: The TMDB API key is already built into the program, so no additional setup is needed!

