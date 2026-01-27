import requests
from datetime import date
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TMDB_BASE_URL = "https://api.themoviedb.org/3"

session = requests.Session()

retries = Retry(
    total=5,
    backoff_factor=1.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)

adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)

session.headers.update({
    "Accept": "application/json",
    "User-Agent": "MovieOpinionMeter/1.0",
})


def fetch_genres():
    r = session.get(
        f"{TMDB_BASE_URL}/genre/movie/list",
        params={"api_key": settings.TMDB_API_KEY},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["genres"]


def fetch_indian_recent_released_movies(page=1):
    one_year_ago = date.today().replace(year=date.today().year - 1)

    r = session.get(
        f"{TMDB_BASE_URL}/discover/movie",
        params={
            "api_key": settings.TMDB_API_KEY,
            "region": "IN",
            "with_original_language": "hi|te|ta|ml|kn",
            "primary_release_date.gte": one_year_ago.isoformat(),
            "primary_release_date.lte": date.today().isoformat(),
            "sort_by": "popularity.desc",
            "page": page,
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def fetch_indian_upcoming_movies(page=1):
    r = session.get(
        f"{TMDB_BASE_URL}/discover/movie",
        params={
            "api_key": settings.TMDB_API_KEY,
            "region": "IN",
            "with_original_language": "hi|te|ta|ml|kn",
            "primary_release_date.gte": date.today().isoformat(),
            "sort_by": "popularity.desc",
            "page": page,
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()



def fetch_movie_by_id(tmdb_id):
    r = session.get(
        f"{TMDB_BASE_URL}/movie/{tmdb_id}",
        params={"api_key": settings.TMDB_API_KEY},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def fetch_movie_full(tmdb_id):
    r = session.get(
        f"{TMDB_BASE_URL}/movie/{tmdb_id}",
        params={
            "api_key": settings.TMDB_API_KEY,
            "append_to_response": "credits",
        },
        timeout=25,
    )
    r.raise_for_status()
    return r.json()

def fetch_person_details(tmdb_person_id):
    r = session.get(
        f"{TMDB_BASE_URL}/person/{tmdb_person_id}",
        params={"api_key": settings.TMDB_API_KEY},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()
