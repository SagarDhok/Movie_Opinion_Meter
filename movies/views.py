# movies/views.py - FIXED VERSION
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from .models import (Movie, Genre, MovieVote, Watchlist, Person, 
                     Cast, Crew, MovieReview, ReviewLike, ReviewComment, CommentLike)
from .forms import MovieReviewForm, ReviewCommentForm
from collections import defaultdict


def home(request):
    """
    Main homepage with smart movie sections.
    
    Handles search, filtering by genre and release status.
    All filtering and pagination done server-side.
    """
    search_query = request.GET.get("search", "").strip()
    genre_filter = request.GET.get("genre", "").strip()
    status_filter = request.GET.get("released", "").strip()
    page_number = request.GET.get("page", "1")

    # Base queryset with optimized prefetch
    base_qs = Movie.objects.all().prefetch_related("categories")
    movies_qs = base_qs

    # Apply filters server-side
    if search_query:
        movies_qs = movies_qs.filter(title__icontains=search_query)

    if genre_filter:
        movies_qs = movies_qs.filter(categories__id=genre_filter).distinct()

    if status_filter == "released":
        movies_qs = movies_qs.filter(is_released=True)
    elif status_filter == "upcoming":
        movies_qs = movies_qs.filter(is_released=False)

    # If any filters applied, show filtered results
    if search_query or genre_filter or status_filter:
        paginator = Paginator(movies_qs.order_by("-release_date"), 24)
        page_obj = paginator.get_page(page_number)

        return render(request, "movies/home.html", {
            "section_title": "Search Results",
            "movies": page_obj.object_list,
            "page_obj": page_obj,
            "genres": Genre.objects.all(),
        })

    # Default view: paginated all movies
    all_movies = base_qs.order_by("-is_released", "-release_date")
    paginator = Paginator(all_movies, 24)
    page_obj = paginator.get_page(page_number)

    context = {
        "movies": page_obj.object_list,
        "page_obj": page_obj,
        "genres": Genre.objects.all(),
    }

    # Smart sections only on first page
    if str(page_number) == "1":
        today = date.today()
        soon_limit = today + timedelta(days=60)
        recent_limit = today - timedelta(days=120)

        # Trending: recent movies with most votes
        context["trending_movies"] = Movie.objects.filter(
            is_released=True,
            release_date__gte=recent_limit
        ).prefetch_related("categories").annotate(
            vote_count=Count("votes")
        ).order_by("-vote_count", "-release_date")[:12]
        
        # Latest released
        context["latest_released_movies"] = Movie.objects.filter(
            is_released=True
        ).prefetch_related("categories").order_by("-release_date")[:12]
        
        # Coming soon (next 60 days)
        context["coming_soon_movies"] = Movie.objects.filter(
            is_released=False,
            release_date__isnull=False,
            release_date__lte=soon_limit
        ).prefetch_related("categories").order_by("release_date")[:12]
        
        # Major upcoming (after 60 days)
        context["major_upcoming_movies"] = Movie.objects.filter(
            is_released=False,
            release_date__isnull=False,
            release_date__gt=soon_limit
        ).prefetch_related("categories").order_by("release_date")[:12]

    return render(request, "movies/home.html", context)


def movie_detail(request, movie_id):
    """
    Movie detail page with voting, reviews, and comments.
    
    All data processing done server-side.
    Uses Django forms for reviews and comments.
    """
    if not request.user.is_authenticated:
        messages.warning(request, "Please login to access the movie detail page.")
        return redirect(f"{reverse('login')}?next={request.path}")

    # Fetch movie with optimized queries
    movie = get_object_or_404(
        Movie.objects.prefetch_related(
            "categories",
            "cast__person",
            "crew__person",
        ),
        id=movie_id,
    )

    # Group crew roles by person
    ROLE_PRIORITY = ["Director", "Producer", "Writer", "Screenplay", 
                     "Story", "Executive Producer"]
    
    crew_map = defaultdict(set)
    for crew in movie.crew.all():
        crew_map[crew.person].add(crew.job)

    def sort_roles(roles):
        return sorted(
            roles,
            key=lambda r: ROLE_PRIORITY.index(r) if r in ROLE_PRIORITY else len(ROLE_PRIORITY)
        )

    def person_priority(jobs):
        for role in ROLE_PRIORITY:
            if role in jobs:
                return ROLE_PRIORITY.index(role)
        return len(ROLE_PRIORITY)

    grouped_crew = sorted(
        [{"person": person, "jobs": sort_roles(list(jobs))}
         for person, jobs in crew_map.items()],
        key=lambda x: person_priority(x["jobs"])
    )

    # Calculate vote statistics server-side
    vote_stats_qs = MovieVote.objects.filter(
        movie=movie
    ).values("vote").annotate(count=Count("id"))
    
    vote_counts = {x["vote"]: x["count"] for x in vote_stats_qs}
    for key in ["bad", "average", "good", "masterpiece"]:
        vote_counts.setdefault(key, 0)

    total_votes = sum(vote_counts.values())
    
    def pct(x):
        return round((x / total_votes) * 100) if total_votes > 0 else 0

    # Get current user's vote
    user_vote = MovieVote.objects.filter(
        user=request.user, 
        movie=movie
    ).first()
    
    # Check if movie in watchlist
    in_watchlist = Watchlist.objects.filter(
        user=request.user, 
        movie=movie
    ).exists()

    # Fetch reviews with optimized queries
    reviews_qs = MovieReview.objects.filter(movie=movie).select_related(
        "user"
    ).prefetch_related(
        Prefetch(
            "likes", 
            queryset=ReviewLike.objects.filter(user=request.user), 
            to_attr="user_likes"
        ),
        Prefetch(
            "comments",
            queryset=ReviewComment.objects.select_related("user").order_by("created_at")
        )
    ).order_by("-created_at")

    my_review = None
    other_reviews = []

    for review in reviews_qs:
        # Get user's vote on this movie
        review.user_vote = MovieVote.objects.filter(
            movie=movie, 
            user=review.user
        ).first()
        
        # Calculate likes
        review.like_count = review.likes.count()
        review.is_liked = bool(review.user_likes)
        
        # Separate own review from others
        if review.user == request.user:
            my_review = review
        else:
            other_reviews.append(review)

    context = {
        "movie": movie,
        "grouped_crew": grouped_crew,
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
        "my_review": my_review,
        "other_reviews": other_reviews,
    }

    return render(request, "movies/detail.html", context)


@login_required
def vote_movie(request, movie_id):
    """
    Handle movie voting.
    
    POST-only endpoint that creates/updates/deletes user votes.
    Redirects back to movie detail page.
    """
    if request.method != "POST":
        return redirect('movie-detail', movie_id=movie_id)
    
    movie = get_object_or_404(Movie, id=movie_id)
    vote = request.POST.get("vote", "").strip().lower()

    allowed_votes = {"bad", "average", "good", "masterpiece", "remove"}

    if vote not in allowed_votes:
        messages.error(request, "Invalid vote option")
        return redirect('movie-detail', movie_id=movie_id)

    # Remove vote
    if vote == "remove":
        deleted_count = MovieVote.objects.filter(
            user=request.user, 
            movie=movie
        ).delete()[0]
        
        if deleted_count:
            messages.success(request, "Vote removed successfully")
        return redirect('movie-detail', movie_id=movie_id)

    # Add or update vote
    MovieVote.objects.update_or_create(
        user=request.user,
        movie=movie,
        defaults={"vote": vote}
    )
    messages.success(request, f"Voted: {vote.title()}")
    
    return redirect('movie-detail', movie_id=movie_id)


@login_required
def toggle_watchlist(request, movie_id):
    """
    Toggle movie in user's watchlist.
    
    POST-only endpoint that adds/removes movie from watchlist.
    """
    if request.method != "POST":
        return redirect('movie-detail', movie_id=movie_id)
    
    movie = get_object_or_404(Movie, id=movie_id)
    watchlist_item = Watchlist.objects.filter(
        user=request.user, 
        movie=movie
    )

    if watchlist_item.exists():
        watchlist_item.delete()
        messages.info(request, f"Removed '{movie.title}' from watchlist")
    else:
        Watchlist.objects.create(user=request.user, movie=movie)
        messages.success(request, f"Added '{movie.title}' to watchlist")

    return redirect('movie-detail', movie_id=movie_id)


@login_required
def watchlist_page(request):
    """
    Display user's watchlist.
    
    Shows all movies user has saved to watchlist.
    """
    watchlist_qs = Watchlist.objects.filter(
        user=request.user
    ).select_related("movie").order_by("-created_at")

    context = {
        "watchlist_movies": watchlist_qs,
        "watchlist_count": watchlist_qs.count(),
    }

    return render(request, "movies/watchlist.html", context)


@login_required
def submit_review(request, movie_id):
    """
    Submit or update movie review.
    
    Uses Django ModelForm for validation.
    Handles both new reviews and updates to existing reviews.
    """
    movie = get_object_or_404(Movie, id=movie_id)
    
    if request.method != "POST":
        return redirect('movie-detail', movie_id=movie_id)

    # Check if user already has a review
    existing_review = MovieReview.objects.filter(
        user=request.user, 
        movie=movie
    ).first()
    
    # Bind form to existing review or create new
    form = MovieReviewForm(request.POST, instance=existing_review)
    
    if form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.movie = movie
        review.save()
        
        if existing_review:
            messages.success(request, "Review updated successfully")
        else:
            messages.success(request, "Review submitted successfully")
    else:
        # Display validation errors
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)

    return redirect('movie-detail', movie_id=movie_id)


@login_required
def delete_review(request, movie_id):
    """
    Delete user's review.
    
    POST-only endpoint for security.
    """
    if request.method != "POST":
        return redirect('movie-detail', movie_id=movie_id)
    
    movie = get_object_or_404(Movie, id=movie_id)
    deleted_count = MovieReview.objects.filter(
        movie=movie, 
        user=request.user
    ).delete()[0]
    
    if deleted_count:
        messages.success(request, "Review deleted successfully")
    else:
        messages.error(request, "Review not found")
    
    return redirect('movie-detail', movie_id=movie_id)


@login_required
def toggle_review_like(request, review_id):
    """
    Toggle like on a review.
    
    POST-only endpoint that adds/removes like.
    """
    if request.method != "POST":
        review = get_object_or_404(MovieReview, id=review_id)
        return redirect('movie-detail', movie_id=review.movie.id)
    
    review = get_object_or_404(MovieReview, id=review_id)
    like_obj = ReviewLike.objects.filter(
        user=request.user, 
        review=review
    )

    if like_obj.exists():
        like_obj.delete()
    else:
        ReviewLike.objects.create(user=request.user, review=review)

    return redirect('movie-detail', movie_id=review.movie.id)


@login_required
def review_likes_list(request, review_id):
    """
    Display list of users who liked a review.
    
    Used for showing likes in a modal/popup.
    """
    review = get_object_or_404(MovieReview, id=review_id)

    likes = review.likes.select_related("user").order_by("-created_at")

    return render(
        request,
        "movies/likes_modal.html",
        {"likes": likes}
    )


@login_required
def add_comment(request, review_id):
    """
    Add comment to a review.
    
    Uses Django form for validation.
    """
    if request.method != "POST":
        review = get_object_or_404(MovieReview, id=review_id)
        return redirect('movie-detail', movie_id=review.movie.id)
    
    review = get_object_or_404(MovieReview, id=review_id)
    form = ReviewCommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.review = review
        comment.save()
        messages.success(request, "Comment added")
    else:
        for error in form.errors.get('text', []):
            messages.error(request, error)

    return redirect('movie-detail', movie_id=review.movie.id)


@login_required
def toggle_comment_like(request, comment_id):
    """
    Toggle like on a comment.
    
    POST-only endpoint.
    """
    if request.method != "POST":
        comment = get_object_or_404(ReviewComment, id=comment_id)
        return redirect('movie-detail', movie_id=comment.review.movie.id)
    
    comment = get_object_or_404(ReviewComment, id=comment_id)
    like_obj = CommentLike.objects.filter(
        user=request.user, 
        comment=comment
    )

    if like_obj.exists():
        like_obj.delete()
    else:
        CommentLike.objects.create(user=request.user, comment=comment)

    return redirect('movie-detail', movie_id=comment.review.movie.id)


@login_required
def reply_comment(request, comment_id):
    """
    Reply to a comment.
    
    Creates nested comment with parent reference.
    """
    if request.method != "POST":
        parent = get_object_or_404(ReviewComment, id=comment_id)
        return redirect('movie-detail', movie_id=parent.review.movie.id)
    
    parent = get_object_or_404(ReviewComment, id=comment_id)
    form = ReviewCommentForm(request.POST)
    
    if form.is_valid():
        reply = form.save(commit=False)
        reply.user = request.user
        reply.review = parent.review
        reply.parent = parent
        reply.save()
        messages.success(request, "Reply added")
    else:
        for error in form.errors.get('text', []):
            messages.error(request, error)

    return redirect('movie-detail', movie_id=parent.review.movie.id)


def person_detail(request, person_id):
    """
    Display person (actor/crew) detail page.
    
    Shows filmography and biography.
    All data fetched server-side.
    """
    person = get_object_or_404(Person, id=person_id)

    # Get movies where person acted
    acted_movies = Cast.objects.filter(
        person=person
    ).select_related("movie")
    
    # Get movies where person was crew
    crew_movies = Crew.objects.filter(
        person=person
    ).select_related("movie")

    context = {
        "person": person,
        "acted_movies": acted_movies,
        "crew_movies": crew_movies,
    }

    return render(request, "movies/person_detail.html", context)