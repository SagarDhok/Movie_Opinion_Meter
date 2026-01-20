from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Count
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import date, timedelta

from .models import Movie, Genre, MovieVote, Watchlist, Person, Cast, Crew


def home(request):
    # ===============================
    # FILTERS (SEARCH / GENRE / STATUS)
    # ===============================
    search_query = request.GET.get("search", "").strip()
    genre_filter = request.GET.get("genre", "")
    status_filter = request.GET.get("released", "")
    page_number = request.GET.get("page", "1")

    movies_qs = Movie.objects.all().prefetch_related("categories")

    if search_query:
        movies_qs = movies_qs.filter(title__icontains=search_query)

    if genre_filter:
        movies_qs = movies_qs.filter(categories__id=genre_filter)

    if status_filter == "released":
        movies_qs = movies_qs.filter(is_released=True)
    elif status_filter == "upcoming":
        movies_qs = movies_qs.filter(is_released=False)

    # ===============================
    # IF FILTERS → ONLY GRID VIEW
    # ===============================
    if search_query or genre_filter or status_filter:
        paginator = Paginator(movies_qs.order_by("-release_date"), 24)
        page_obj = paginator.get_page(page_number)

        return render(request, "movies/home.html", {
            "section_title": "Search Results",
            "movies": page_obj.object_list,
            "page_obj": page_obj,
            "genres": Genre.objects.all(),
        })

    # ===============================
    # PAGINATED ALL MOVIES (ALWAYS)
    # ===============================
    all_movies = Movie.objects.order_by("-is_released", "-release_date")
    paginator = Paginator(all_movies, 24)
    page_obj = paginator.get_page(page_number)

    context = {
        "movies": page_obj.object_list,
        "page_obj": page_obj,
        "genres": Genre.objects.all(),
    }

    # ===============================
    # SMART SECTIONS → ONLY PAGE 1
    # ===============================
    if str(page_number) == "1":
        today = date.today()
        soon_limit = today + timedelta(days=60)
        recent_limit = today - timedelta(days=120)

        # 🔥 Trending This Week (recent + voted)
        trending_movies = (
            Movie.objects
            .filter(
                is_released=True,
                release_date__gte=recent_limit
            )
            .annotate(vote_count=Count("votes"))
            .order_by("-vote_count", "-release_date")[:12]
        )

        # 🎬 Latest Released
        latest_released_movies = (
            Movie.objects
            .filter(is_released=True)
            .order_by("-release_date")[:12]
        )

        # ⏳ Coming Very Soon (next 60 days)
        coming_soon_movies = (
            Movie.objects
            .filter(
                is_released=False,
                release_date__isnull=False,
                release_date__lte=soon_limit
            )
            .order_by("release_date")[:12]
        )

        # 🚀 Major Upcoming (after 60 days)
        major_upcoming_movies = (
            Movie.objects
            .filter(
                is_released=False,
                release_date__gt=soon_limit
            )
            .order_by("release_date")[:12]
        )

        context.update({
            "trending_movies": trending_movies,
            "latest_released_movies": latest_released_movies,
            "coming_soon_movies": coming_soon_movies,
            "major_upcoming_movies": major_upcoming_movies,
        })

    return render(request, "movies/home.html", context)




def movie_detail(request, movie_id):

    # 🔒 AUTH CHECK
    if not request.user.is_authenticated:
        messages.warning(
            request,
            "Please login to access the movie detail page."
        )
        login_url = reverse("login")  # 👈 resolves to /users/login/
        return redirect(f"{login_url}?next={request.path}")
    movie = get_object_or_404(
        Movie.objects.prefetch_related("categories", "cast", "crew"),
        id=movie_id,
    )

    # Aggregated votes
    vote_stats = (
        MovieVote.objects
        .filter(movie=movie)
        .values("vote")
        .annotate(count=Count("id"))
    )

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

@login_required
def toggle_watchlist(request, movie_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    movie = Movie.objects.get(id=movie_id)

    qs = Watchlist.objects.filter(
        user=request.user,
        movie=movie
    )

    if qs.exists():
        qs.delete()
        return JsonResponse({
            "status": "removed",
            "message": "Removed from watchlist"
        })

    Watchlist.objects.create(
        user=request.user,
        movie=movie
    )

    return JsonResponse({
        "status": "added",
        "message": "Added to watchlist"
    })


@login_required
def watchlist_page(request):
    watchlist_qs = (
        Watchlist.objects
        .filter(user=request.user)
        .select_related("movie")
        .order_by("-created_at")
    )

    context = {
        "watchlist_movies": watchlist_qs,
        "watchlist_count": watchlist_qs.count(),
    }

    return render(request, "movies/watchlist.html", context)




def person_detail(request, person_id):
    person = get_object_or_404(Person, id=person_id)

    acted_movies = (
        Cast.objects
        .filter(person=person)
        .select_related("movie")
    )

    crew_movies = (
        Crew.objects
        .filter(person=person)
        .select_related("movie")
    )

    context = {
        "person": person,
        "acted_movies": acted_movies,
        "crew_movies": crew_movies,
    }

    return render(request, "movies/person_detail.html", context)
