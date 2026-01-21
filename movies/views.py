from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Count
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import date, timedelta
from django.views.decorators.http import require_POST
from .models import Movie, Genre, MovieVote, Watchlist, Person, Cast, Crew, MovieReview


def home(request):
    # ===============================
    # FILTERS (SEARCH / GENRE / STATUS)
    # ===============================
    search_query = request.GET.get("search", "").strip()
    genre_filter = request.GET.get("genre", "").strip()
    status_filter = request.GET.get("released", "").strip()
    page_number = request.GET.get("page", "1")

    base_qs = (
        Movie.objects
        .all()
        .prefetch_related("categories")
    )

    movies_qs = base_qs

    if search_query:
        movies_qs = movies_qs.filter(title__icontains=search_query)

    if genre_filter:
        movies_qs = movies_qs.filter(categories__id=genre_filter).distinct()

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
    all_movies = base_qs.order_by("-is_released", "-release_date")

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
            .prefetch_related("categories")
            .annotate(vote_count=Count("votes"))
            .order_by("-vote_count", "-release_date")[:12]
        )

        # 🎬 Latest Released
        latest_released_movies = (
            Movie.objects
            .filter(is_released=True)
            .prefetch_related("categories")
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
            .prefetch_related("categories")
            .order_by("release_date")[:12]
        )

        # 🚀 Major Upcoming (after 60 days)
        major_upcoming_movies = (
            Movie.objects
            .filter(
                is_released=False,
                release_date__isnull=False,
                release_date__gt=soon_limit
            )
            .prefetch_related("categories")
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
        messages.warning(request, "Please login to access the movie detail page.")
        login_url = reverse("login")
        return redirect(f"{login_url}?next={request.path}")

    movie = get_object_or_404(
        Movie.objects.prefetch_related("categories", "cast", "crew"),
        id=movie_id,
    )

    vote_stats_qs = (
        MovieVote.objects
        .filter(movie=movie)
        .values("vote")
        .annotate(count=Count("id"))
    )

    vote_counts = {x["vote"]: x["count"] for x in vote_stats_qs}
    total_votes = sum(vote_counts.values())

    # ensure all exist
    for key in ["bad", "average", "good", "masterpiece"]:
        vote_counts.setdefault(key, 0)

    def pct(x):
        return round((x / total_votes) * 100) if total_votes > 0 else 0


    user_vote = MovieVote.objects.filter(
        user=request.user, movie=movie
    ).first()

    in_watchlist = Watchlist.objects.filter(
        user=request.user, movie=movie
    ).exists()

    
    reviews = (
        MovieReview.objects
        .filter(movie=movie)
        .select_related("user")
        .prefetch_related("likes", "comments")
    )



    context = {
        "movie": movie,
        "vote_counts": vote_counts,
        "total_votes": total_votes,
        "vote_percents": {
            "bad": pct(vote_counts["bad"]),
            "average": pct(vote_counts["average"]),
            "good": pct(vote_counts["good"]),
            "masterpiece": pct(vote_counts["masterpiece"]),
        },
        "user_vote": user_vote.vote if user_vote else "",
        "in_watchlist": in_watchlist,
          "reviews": reviews,
    }

    return render(request, "movies/detail.html", context)


@login_required
@require_POST
def toggle_watchlist(request, movie_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    movie = get_object_or_404(Movie, id=movie_id)

    qs = Watchlist.objects.filter(user=request.user, movie=movie)

    if qs.exists():
        qs.delete()
        return JsonResponse({
            "status": "removed",
            "message": "Removed from watchlist"
        })

    Watchlist.objects.create(user=request.user, movie=movie)

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


@login_required
@require_POST
def vote_movie(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    vote = request.POST.get("vote", "").strip().lower()

    allowed = {"bad", "average", "good", "masterpiece"}

    # =========================
    # REMOVE VOTE (TOGGLE OFF)
    # =========================
    if vote == "remove":
        MovieVote.objects.filter(
            user=request.user,
            movie=movie
        ).delete()

        stats = (
            MovieVote.objects
            .filter(movie=movie)
            .values("vote")
            .annotate(count=Count("id"))
        )

    # =========================
    # ADD / CHANGE VOTE
    # =========================
    elif vote in allowed:
        MovieVote.objects.update_or_create(
            user=request.user,
            movie=movie,
            defaults={"vote": vote}
        )

        stats = (
            MovieVote.objects
            .filter(movie=movie)
            .values("vote")
            .annotate(count=Count("id"))
        )

    else:
        return JsonResponse({"error": "Invalid vote"}, status=400)

    # =========================
    # BUILD RESPONSE
    # =========================
    vote_counts = {x["vote"]: x["count"] for x in stats}
    total_votes = sum(vote_counts.values())

    for key in allowed:
        vote_counts.setdefault(key, 0)

    def pct(x):
        return round((x / total_votes) * 100) if total_votes > 0 else 0

    return JsonResponse({
        "status": "ok",
        "user_vote": vote if vote != "remove" else "",
        "total_votes": total_votes,
        "counts": vote_counts,
        "percents": {
            "bad": pct(vote_counts["bad"]),
            "average": pct(vote_counts["average"]),
            "good": pct(vote_counts["good"]),
            "masterpiece": pct(vote_counts["masterpiece"]),
        }
    })




@login_required
@require_POST
def submit_review(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    rating = request.POST.get("rating")
    review_text = request.POST.get("review_text", "").strip()

    if not rating or not review_text:
        return JsonResponse({"error": "Rating and review are required"}, status=400)

    rating = int(rating)
    if rating < 1 or rating > 5:
        return JsonResponse({"error": "Invalid rating"}, status=400)

    review, created = MovieReview.objects.update_or_create(
        user=request.user,
        movie=movie,
        defaults={
            "rating": rating,
            "review_text": review_text,
        }
    )

    return JsonResponse({
        "status": "ok",
        "created": created,
    })
