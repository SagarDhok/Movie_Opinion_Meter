from django.urls import path
from . import views,views_ai
from movies.admin_sync import sync_tmdb

urlpatterns = [
    path("", views.home, name="movies-home"),

    path("movie/<int:movie_id>/", views.movie_detail, name="movie-detail"),
    path("movie/<int:movie_id>/vote/", views.vote_movie, name="vote-movie"),
    path("movie/<int:movie_id>/watchlist/", views.toggle_watchlist, name="toggle-watchlist"),

    path("movie/<int:movie_id>/review/", views.submit_review, name="submit-review"),
    path("movie/<int:movie_id>/review/delete/", views.delete_review, name="delete-review"),

    path("reviews/<int:review_id>/like/", views.toggle_review_like, name="toggle-review-like"),
    path("reviews/<int:review_id>/likes/", views.review_likes_list, name="review-likes-list"),



    path("person/<int:person_id>/", views.person_detail, name="person-detail"),

    path("watchlist/", views.watchlist_page, name="watchlist"),
    path("reviews/<int:review_id>/comments-page/", views.comments_page, name="comments-page"),
    path("reviews/<int:review_id>/comments/add/", views.add_comment_page, name="add-comment-page"),
    path("comments/<int:comment_id>/reply/", views.reply_comment_page, name="reply-comment-page"),
    path("comments/<int:comment_id>/delete/", views.delete_comment_page, name="delete-comment-page"),
    path("movie/<int:movie_id>/hype/", views.hype_vote_movie, name="hype-vote-movie"),
    path("movie/<int:movie_id>/reviews/", views.all_reviews_page, name="all-reviews"),
    path("movie/<int:movie_id>/ai/assist/", views_ai.ai_review_assistant, name="ai-review-assistant"),
    path("movie/<int:movie_id>/ai/pros-cons/",views_ai.ai_pros_cons, name="ai-pros-cons"),
    path("review/<int:review_id>/ai/pros-cons/", views_ai.ai_pros_cons_review, name="ai-pros-cons-review"),





]
