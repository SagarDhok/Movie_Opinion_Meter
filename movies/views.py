from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Movie, Genre,Movie, MovieVote, Watchlist
from django.db.models import Count


def home(request):
    movies = Movie.objects.prefetch_related("categories").all()
    genres = Genre.objects.all()

    # 🔍 Search by title
    search_query = request.GET.get("search")
    if search_query:
        movies = movies.filter(title__icontains=search_query)

    # 🎭 Filter by genre
    genre_name = request.GET.get("genre")
    if genre_name:
        movies = movies.filter(categories__name=genre_name)

    # 📅 Filter by release status
    released = request.GET.get("released")
    if released == "true":
        movies = movies.filter(is_released=True)
    elif released == "false":
        movies = movies.filter(is_released=False)

    movies = movies.distinct().order_by("-release_date")

    # 📄 PAGINATION
    paginator = Paginator(movies, 18)  
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "movies": page_obj,   
        "genres": genres,
        "page_obj": page_obj,
    }
    return render(request, "movies/home.html", context)




def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    # Aggregated votes
    vote_stats = (
        MovieVote.objects
        .filter(movie=movie)
        .values("vote")
        .annotate(count=Count("id"))
    )

    user_vote = None
    in_watchlist = False

    if request.user.is_authenticated:
        user_vote = MovieVote.objects.filter(
            user=request.user, movie=movie
        ).first()

        in_watchlist = Watchlist.objects.filter(
            user=request.user, movie=movie
        ).exists()

    

    context = {
        "movie": movie,
        "vote_stats": vote_stats,
        "user_vote": user_vote,
        "in_watchlist": in_watchlist,
    }
    return render(request, "movies/detail.html", context)






