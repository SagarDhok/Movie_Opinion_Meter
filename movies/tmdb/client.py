import requests
from django.conf import settings

TMDB_BASE_URL = "https://api.themoviedb.org/3"


def fetch_genres():
    response = requests.get( f"{TMDB_BASE_URL}/genre/movie/list",
                            params={"api_key": settings.TMDB_API_KEY},
                            timeout=10,)
    response.raise_for_status()
#     response.raise_for_status()
# If status is 200 OK → continue
# If 401 / 403 / 500 → crash immediately

    return response.json()["genres"]

# TMDB response 
# json() = {
#   "genres": [
#     {"id": 28, "name": "Action"},
#     {"id": 18, "name": "Drama"}
#   ]
# }

# return response.json()["genres"]
# [
#   {"id": 28, "name": "Action"},
#   {"id": 18, "name": "Drama"}
# ]


def fetch_indian_movies(page=1, language="hi"):
# /discover/movie?
# api_key=XXX
# &region=IN
# &with_original_language=hi
# &sort_by=popularity.desc
# &page=1
    response = requests.get(
        f"{TMDB_BASE_URL}/discover/movie",
        params={
            "api_key": settings.TMDB_API_KEY,
            "region": "IN",
            "with_original_language": language,
            "sort_by": "popularity.desc",
            "page": page,
        },
        timeout=10,
    )

    response.raise_for_status()
    return response.json()

# fetch_indian_movies
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
#     ...
#   ],
#   "total_pages": 500,
#   "total_results": 10000
# }



# client.py
# → HTTP request (requests.get)
# → TMDB server
# → HTTP response (JSON)
# → Python dict/list (RAM)
# → return to sync.py
