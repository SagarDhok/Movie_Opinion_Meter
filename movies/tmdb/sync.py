import time
from datetime import date
from movies.models import Movie, Genre
from .client import (
    fetch_genres,
    fetch_indian_recent_released_movies,
    fetch_indian_upcoming_movies,
    fetch_movie_by_id,
)


IMPORTANT_TMDB_IDS = [

]


def sync_genres():
    genre_map = {}

    for g in fetch_genres():
        genre, _ = Genre.objects.get_or_create(name=g["name"])
        genre_map[g["id"]] = genre

    return genre_map


def save_movie_to_db(movie_data, genre_map):
    release_date = movie_data.get("release_date")
    is_released = False

    if release_date:
        try:
            is_released = date.fromisoformat(release_date) <= date.today()
        except ValueError:
            release_date = None

    movie, _ = Movie.objects.update_or_create(
        tmdb_id=movie_data["id"],
        defaults={
            "title": movie_data.get("title", ""),
            "poster_path": movie_data.get("poster_path"),
            "release_date": release_date,
            "is_released": is_released,
            "overview": movie_data.get("overview", ""),
        },
    )

    genre_ids = movie_data.get("genre_ids") or []
    movie.categories.set(
        [genre_map[g] for g in genre_ids if g in genre_map]
    )

    return movie


def sync_priority_movies(genre_map):
    for tmdb_id in IMPORTANT_TMDB_IDS:
        try:
            movie_data = fetch_movie_by_id(tmdb_id)
            save_movie_to_db(movie_data, genre_map)
            time.sleep(0.4)
        except Exception:
            continue

def sync_all_movies(limit=50):
    print("🎬 Syncing Indian movies (last 1 year + upcoming)")

    genre_map = sync_genres()

    released_limit = 30
    upcoming_limit = 20

    synced_released = 0
    synced_upcoming = 0

    # -------- Released (last 1 year) --------
    page = 1
    while synced_released < released_limit:
        data = fetch_indian_recent_released_movies(page)
        results = data.get("results", [])

        if not results:
            break

        for movie_data in results:
            if synced_released >= released_limit:
                break

            save_movie_to_db(movie_data, genre_map)
            synced_released += 1
            time.sleep(0.3)

        page += 1

    # -------- Upcoming --------
    page = 1
    while synced_upcoming < upcoming_limit:
        data = fetch_indian_upcoming_movies(page)
        results = data.get("results", [])

        if not results:
            break

        for movie_data in results:
            if synced_upcoming >= upcoming_limit:
                break

            save_movie_to_db(movie_data, genre_map)
            synced_upcoming += 1
            time.sleep(0.3)

        page += 1

    total = synced_released + synced_upcoming
    print(
        f"✅ Sync complete — {total} movies "
        f"({synced_released} released, {synced_upcoming} upcoming)"
    )
