"""
Utility Modules

This package contains utility functions for the recommender system,
including image downloading and API clients.
"""

from .image_downloader import (
    download_movie_image,
    image_exists,
    get_image_path,
    download_movie_images_batch,
    ensure_movie_images
)
from .api_client import (
    search_movie_tmdb,
    get_movie_overview,
    get_movie_poster_url
)

__all__ = [
    'download_movie_image',
    'image_exists',
    'get_image_path',
    'download_movie_images_batch',
    'ensure_movie_images',
    'search_movie_tmdb',
    'get_movie_overview',
    'get_movie_poster_url'
]

