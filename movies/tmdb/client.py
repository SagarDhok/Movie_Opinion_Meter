import requests
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


# 🔥 Popular movies Indians care about (Hollywood + Indian)
def fetch_popular_india(page=1):
    r = session.get(
        f"{TMDB_BASE_URL}/discover/movie",
        params={
            "api_key": settings.TMDB_API_KEY,
            "region": "IN",
            "sort_by": "popularity.desc",
            "vote_count.gte": 100,
            "page": page,
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


# 🎬 Now playing in India
def fetch_now_playing_india(page=1):
    r = session.get(
        f"{TMDB_BASE_URL}/movie/now_playing",
        params={
            "api_key": settings.TMDB_API_KEY,
            "region": "IN",
            "page": page,
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


# 🚀 Upcoming India releases (big Hollywood + Indian)
def fetch_upcoming_india(page=1):
    r = session.get(
        f"{TMDB_BASE_URL}/movie/upcoming",
        params={
            "api_key": settings.TMDB_API_KEY,
            "region": "IN",
            "page": page,
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


# 🔥 Trending (global pop culture)
def fetch_trending_week(page=1):
    r = session.get(
        f"{TMDB_BASE_URL}/trending/movie/week",
        params={
            "api_key": settings.TMDB_API_KEY,
            "page": page,
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


# 🇮🇳 Indian regional cinema
def fetch_indian_language_movies(page=1):
    r = session.get(
        f"{TMDB_BASE_URL}/discover/movie",
        params={
            "api_key": settings.TMDB_API_KEY,
            "with_original_language": "hi|te|ta|ml|kn",
            "sort_by": "popularity.desc",
            "vote_count.gte": 50,
            "page": page,
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()
