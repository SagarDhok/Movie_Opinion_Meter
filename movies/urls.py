from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="movies-home"),

    path("movie/<int:movie_id>/", views.movie_detail, name="movie-detail"),
    path("movie/<int:movie_id>/vote/", views.vote_movie, name="vote-movie"),
    path("movie/<int:movie_id>/watchlist/", views.toggle_watchlist, name="toggle-watchlist"),

    path("movie/<int:movie_id>/review/", views.submit_review, name="submit-review"),
    path("movie/<int:movie_id>/review/delete/", views.delete_review, name="delete-review"),

    path("reviews/<int:review_id>/like/", views.toggle_review_like, name="toggle-review-like"),
    path("reviews/<int:review_id>/likes/", views.review_likes_list, name="review-likes-list"),

    path("reviews/<int:review_id>/comments/add/", views.add_comment, name="add-comment"),
    path("comments/<int:comment_id>/like/", views.toggle_comment_like, name="toggle-comment-like"),
    path("comments/<int:comment_id>/reply/", views.reply_comment, name="reply-comment"),

    path("person/<int:person_id>/", views.person_detail, name="person-detail"),
    path("watchlist/", views.watchlist_page, name="watchlist"),
]
