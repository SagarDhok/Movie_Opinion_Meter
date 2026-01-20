from django.urls import path
from . import views

urlpatterns = [
        path("", views.home, name="movies-home"), 
        path("movie/<int:movie_id>/", views.movie_detail, name="movie-detail"),
        path("movie/<int:movie_id>/watchlist/", views.toggle_watchlist, name="toggle-watchlist"),
        path("watchlist/", views.watchlist_page, name="watchlist"),

       path("person/<int:person_id>/", views.person_detail, name="person-detail"),

]
