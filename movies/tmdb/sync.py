import time
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


def sync_all_movies(limit=200):
    print(f"🎬 Syncing Indian + Pop Culture movies (limit={limit})")

    genre_map = sync_genres()
    synced = 0

    # Order matters:
    # 1. Indian popular + Hollywood Indians care about
    # 2. Now playing (India)
    # 3. Upcoming (big franchises show up here)
    # 4. Trending (pure pop culture)
    # 5. Indian regional cinema
    sources = [
        fetch_popular_india,
        fetch_now_playing_india,
        fetch_upcoming_india,
        fetch_trending_week,
        fetch_indian_language_movies,
    ]

    for fetch_fn in sources:
        page = 1

        while synced < limit:
            data = fetch_fn(page)
            results = data.get("results", [])

            if not results:
                break

            for movie_data in results:
                if synced >= limit:
                    break

                save_movie_to_db(movie_data, genre_map)
                synced += 1

                # TMDB safety (VERY IMPORTANT)
                time.sleep(0.25)

            page += 1

    print(f"✅ Sync complete — {synced} movies saved")
