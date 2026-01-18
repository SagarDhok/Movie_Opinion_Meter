# Fetch genres + movies from TMDB → store in DB → connect movie with genres
from datetime import date
from movies.models import Movie, Genre
from .client import fetch_genres, fetch_indian_movies


def sync_popular_movies(pages=5):
    genre_map = {}
#    genre_map = {
#   28: <Genre: Action>,
#   18: <Genre: Drama>
# }

    # 1️⃣ Fetch genres and store them
    for g in fetch_genres():
# fetch genres response = [
#   {"id": 28, "name": "Action"},
#   {"id": 18, "name": "Drama"}
# ]

        genre, _ = Genre.objects.get_or_create(name=g["name"])
        genre_map[g["id"]] = genre


    # 2️⃣ Fetch movies page by page
    for page in range(1, pages + 1):
        data = fetch_indian_movies(page=page)

        for m in data.get("results", []):

# m example:
# {
#   "id": 124,
#   "title": "pushpa",
#   "genre_ids": [38, 18],
#   "release_date": "2026-05-25",
#   "poster_path": "/dbc.jpg"
# }

            release_date = m.get("release_date") or None

# release_date = "2026-05-25" OR None

            is_released = False
# default → not released

            if release_date:
# if date exists, compare with today
                is_released = date.fromisoformat(release_date) <= date.today()

# past date  → True
# future date → False

            movie, _ = Movie.objects.update_or_create(
                tmdb_id=m["id"],
                defaults={
                    "title": m["title"],
                    "poster_path": m.get("poster_path"),
                    "release_date": release_date,
                    "is_released": is_released,
                }
            )

# movie object example:
# Movie(
#   tmdb_id=123,
#   title="RRR",
#   release_date=2022-03-25,
#   is_released=True
# )

            # 3️⃣ Sync genres (ManyToMany)
            new_genres = {genre_map[g] for g in m.get("genre_ids", []) if g in genre_map}
            current_genres = set(movie.categories.all())

            movie.categories.add(*(new_genres - current_genres))
            movie.categories.remove(*(current_genres - new_genres))

# [<Genre: Action>, <Genre: Drama>]
