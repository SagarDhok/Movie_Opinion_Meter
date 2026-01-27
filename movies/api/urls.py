from django.urls import path
from .views import *

urlpatterns = [
    path("movies/", MovieListAPI.as_view()),
    path("movies/<int:movie_id>/", MovieDetailAPI.as_view()),
    path("movies/<int:movie_id>/reviews/", MovieReviewsAPI.as_view()),
    path("movies/<int:movie_id>/vote/", MovieVoteAPI.as_view()),
    path("movies/<int:movie_id>/watchlist/", ToggleWatchlistAPI.as_view()),

    path("reviews/<int:review_id>/like/", ToggleReviewLikeAPI.as_view()),

    path("me/", MeAPI.as_view()),
    path("me/watchlist/", MyWatchlistAPI.as_view()),
]
