from datetime import date
from movies.models import Movie, Genre
from .client import (
    fetch_genres,
    fetch_popular_india,
    fetch_now_playing_india,
    fetch_upcoming_india,
    fetch_trending_week,
    fetch_indian_language_movies,
)


def sync_genres():
    genre_map = {}
    for g in fetch_genres():
        genre, _ = Genre.objects.get_or_create(name=g["name"])
        genre_map[g["id"]] = genre
    return genre_map


def save_movie_to_db(movie_data, genre_map):
    release_date = movie_data.get("release_date") or None
    is_released = False

    if release_date:
        is_released = date.fromisoformat(release_date) <= date.today()

    movie, _ = Movie.objects.update_or_create(
        tmdb_id=movie_data["id"],
        defaults={
            "title": movie_data["title"],
            "poster_path": movie_data.get("poster_path"),
            "release_date": release_date,
            "is_released": is_released,
            "overview": movie_data.get("overview", ""),
        },
    )

    genre_ids = movie_data.get("genre_ids", [])
    movie.categories.set(
        {genre_map[g] for g in genre_ids if g in genre_map}
    )

    return movie


def sync_popular_movies(pages=10):
    genre_map = sync_genres()
    for page in range(1, pages + 1):
        data = fetch_popular_india(page)
        for m in data.get("results", []):
            save_movie_to_db(m, genre_map)


def sync_now_playing(pages=5):
    genre_map = sync_genres()
    for page in range(1, pages + 1):
        data = fetch_now_playing_india(page)
        for m in data.get("results", []):
            save_movie_to_db(m, genre_map)


def sync_upcoming(pages=5):
    genre_map = sync_genres()
    for page in range(1, pages + 1):
        data = fetch_upcoming_india(page)
        for m in data.get("results", []):
            save_movie_to_db(m, genre_map)


def sync_trending(pages=3):
    genre_map = sync_genres()
    for page in range(1, pages + 1):
        data = fetch_trending_week(page)
        for m in data.get("results", []):
            save_movie_to_db(m, genre_map)


def sync_indian_movies(pages=5):
    genre_map = sync_genres()
    for page in range(1, pages + 1):
        data = fetch_indian_language_movies(page)
        for m in data.get("results", []):
            save_movie_to_db(m, genre_map)


def sync_all_movies():
    print("🎬 Syncing Indian + Pop Culture Movies")
    sync_popular_movies()
    sync_now_playing()
    sync_upcoming()
    sync_trending()
    sync_indian_movies()
    print("✅ Sync complete")
