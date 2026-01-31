from django.urls import path
from .views import (
    MovieListAPIView,
    MovieDetailAPIView,
    MovieReviewsAPIView,
    ReviewCreateUpdateAPIView,
    AIRewriteReviewAPIView,
    AIProsConsAPIView,
)

urlpatterns = [
    path("", MovieListAPIView.as_view()),
    path("<int:pk>/", MovieDetailAPIView.as_view()),

    path("<int:movie_id>/reviews/", MovieReviewsAPIView.as_view()),
    path("<int:movie_id>/review/", ReviewCreateUpdateAPIView.as_view()),

    path("<int:movie_id>/ai/rewrite/", AIRewriteReviewAPIView.as_view()),
    path("<int:movie_id>/ai/pros-cons/", AIProsConsAPIView.as_view()),
]
