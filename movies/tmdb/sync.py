# Fetch genres + movies from TMDB → store in DB → connect movie with genres
from movies.models import Movie, Genre
from .client import fetch_genres,fetch_indian_movies


def sync_popular_movies(pages=5):
    genre_map = {}
#    genre_map = {
#   28: <Genre: Action>,
#   18: <Genre: Drama>
# }


    for g in fetch_genres():
# fetch generes response = [
#   {"id": 28, "name": "Action"},
#   {"id": 18, "name": "Drama"}
# ]

        genre, _ = Genre.objects.get_or_create(name=g["name"]) #get_or_create return =(object, created)(<Genre: Action>, True)
        genre_map[g["id"]] = genre


# {
#   "page": 1,
#   "results": [
#     {
#       "id": 123,
#       "title": "RRR",
#       "genre_ids": [28, 18],
#       "release_date": "2022-03-25",
#       "poster_path": "/abc.jpg"
#     },
    # {
#       "id": 124,
#       "title": "pushpa",
#       "genre_ids": [38, 18],
#       "release_date": "2026-05-25",
#       "poster_path": "/dbc.jpg"
#     },
#     ...
#   ],
#   "total_pages": 500,
#   "total_results": 10000
# }->
    for page in range(1, pages + 1):
        data = fetch_indian_movies(page=page)

        for m in data.get("results", []):
            
            movie, _ = Movie.objects.update_or_create(
            tmdb_id=m["id"],      
            defaults={
                "title": m["title"],
                "poster_path": m.get("poster_path"),
                "release_date": m.get("release_date") or None,
                "is_released": bool(m.get("release_date")),
            }
        )
            
#     movie = Movie(
#     id=1,
#     tmdb_id=123,
#     title="RRR",
#     poster_path="/abc.jpg",
#     release_date=date(2022, 3, 25),
#     is_released=True
# )


    
# date present → True
# missing → False
    
            
# m is result movies ->m =  {
#       "id": 123,
#       "title": "RRR",
#       "genre_ids": [28, 18],
#       "release_date": "2022-03-25",
#       "poster_path": "/abc.jpg"
#     },


            new_genres = {genre_map[g] for g in m.get("genre_ids", []) if g in genre_map}
            current_genres = set(movie.categories.all())

            movie.categories.add(*(new_genres - current_genres))
            movie.categories.remove(*(current_genres - new_genres))


             # [<Genre: Action>, <Genre: Drama>]



# ✅ TMDB Sync Flow (Genres + Movies)
# 1) Fetch genres from TMDB

# Call fetch_genres() from client.py

# It returns a list like:

# [{"id": 28, "name": "Action"}, {"id": 18, "name": "Drama"}]

# 2) Save genres in the database + build genre_map

# For each genre g:

# genre, _ = Genre.objects.get_or_create(name=g["name"])
# genre_map[g["id"]] = genre


# genre_map becomes:

# {28: <Genre: Action>, 18: <Genre: Drama>}

# 3) Fetch movies page-by-page

# Loop through pages:

# for page in range(1, pages + 1):
#     data = fetch_indian_movies(page=page)


# Each page gives ~20 movies inside data["results"]

# 4) Save each movie in the database

# For every movie m in results:

# movie, _ = Movie.objects.get_or_create(
#     title=m["title"],
#     defaults={
#         "poster_path": m.get("poster_path"),
#         "release_date": m.get("release_date") or None,
#         "is_released": bool(m.get("release_date")),
#     }
# )


# If movie already exists → it is fetched (no new duplicate)

# If not present → it is created with the default fields

# 5) Attach genres to the movie (ManyToMany)

# TMDB provides genre_ids like:

# [28, 18]


# Convert IDs to Genre objects using the map:

# genres = [genre_map[g] for g in m.get("genre_ids", []) if g in genre_map]


# Save the relationship:

# movie.categories.set(genres)


# ✅ This creates the Movie ↔ Genre connection in the ManyToMany table.
