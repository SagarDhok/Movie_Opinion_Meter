from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch,Q
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from .models import (Movie, Genre, MovieVote, Watchlist, Person, 
                     Cast, Crew, MovieReview, ReviewLike, ReviewComment, MovieHypeVote)
from .forms import MovieReviewForm
from collections import defaultdict



def home(request):

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

    all_movies = base_qs.order_by("-is_released", "-release_date")
    paginator = Paginator(all_movies, 24)
    page_obj = paginator.get_page(page_number)

    context = {
        "movies": page_obj.object_list,
        "page_obj": page_obj,
        "genres": Genre.objects.all(),
    }

    if str(page_number) == "1":
        today = date.today()
        soon_limit = today + timedelta(days=60)
        recent_limit = today - timedelta(days=120)
        
        #trednding section 
        context["trending_movies"] = Movie.objects.filter(
            is_released=True,
            release_date__gte=recent_limit
        ).prefetch_related("categories").annotate(
            vote_count=Count("votes")
        ).order_by("-vote_count", "-release_date")[:12]


        #  Most Hyped (Upcoming) movies
        context["hyped_movies"] = Movie.objects.filter(
            is_released=False
        ).annotate(
            excited_count=Count("hype_votes", filter=Q(hype_votes__vote="excited")),
            total_hype_votes=Count("hype_votes"),
        ).filter(
            total_hype_votes__gt=0
        ).order_by(
            "-excited_count",
            "-total_hype_votes",
            "release_date"
        )[:12]


                
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
        
    
        context["major_upcoming_movies"] = Movie.objects.filter(
            is_released=False,
            release_date__isnull=False,
            release_date__gt=soon_limit
        ).prefetch_related("categories").order_by("release_date")[:12]

    return render(request, "movies/home.html", context)


def movie_detail(request, movie_id):
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

    vote_stats_qs = MovieVote.objects.filter(
        movie=movie
    ).values("vote").annotate(count=Count("id"))
    
    vote_counts = {x["vote"]: x["count"] for x in vote_stats_qs}
    for key in ["bad", "average", "good", "masterpiece"]:
        vote_counts.setdefault(key, 0)

    total_votes = sum(vote_counts.values())
    
    def pct(x):
        return round((x / total_votes) * 100) if total_votes > 0 else 0

   
    user_vote = MovieVote.objects.filter(
        user=request.user, 
        movie=movie
    ).first()

    hype_counts = {"excited": 0, "not_excited": 0}
    hype_score = 0
    hype_not_excited_percent = 0
    user_hype_vote = ""

    if not movie.is_released:
        hype_stats = MovieHypeVote.objects.filter(movie=movie).values("vote").annotate(count=Count("id"))
        hype_counts = {x["vote"]: x["count"] for x in hype_stats}

        hype_counts.setdefault("excited", 0)
        hype_counts.setdefault("not_excited", 0)

        hype_total = hype_counts["excited"] + hype_counts["not_excited"]

        if hype_total > 0:
            hype_score = round((hype_counts["excited"] / hype_total) * 100)
            hype_not_excited_percent = 100 - hype_score
        else:
            hype_score = 0
            hype_not_excited_percent = 0

        hype_obj = MovieHypeVote.objects.filter(movie=movie, user=request.user).first()
        user_hype_vote = hype_obj.vote if hype_obj else ""


    
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
        
        review.user_vote = MovieVote.objects.filter(
            movie=movie, 
            user=review.user
        ).first()
        

        
        review.like_count = review.likes.count()
        review.is_liked = bool(review.user_likes)
        review.comment_count = review.comments.count()

        text = (review.review_text or "").strip()

        line_count = len(text.splitlines())
        char_count = len(text)

        review.show_more = (line_count > 3) or (char_count > 150)

                
        
        if review.user == request.user:
            my_review = review
        else:
            other_reviews.append(review)


    edit_mode = request.GET.get("edit") == "1"

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
         "edit_mode": edit_mode,
          "hype_counts": hype_counts,
    "hype_score": hype_score,
    "user_hype_vote": user_hype_vote,
    "hype_not_excited_percent": hype_not_excited_percent,

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

    movie = get_object_or_404(Movie, id=movie_id)
    
    if request.method != "POST":
        return redirect('movie-detail', movie_id=movie_id)

    existing_review = MovieReview.objects.filter(
        user=request.user, 
        movie=movie
    ).first()
    
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


from django.http import JsonResponse

@login_required
def toggle_review_like(request, review_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Invalid method"}, status=405)

    review = get_object_or_404(MovieReview, id=review_id)

    like_obj = ReviewLike.objects.filter(user=request.user, review=review)

    if like_obj.exists():
        like_obj.delete()
        liked = False
    else:
        ReviewLike.objects.create(user=request.user, review=review)
        liked = True

    like_count = ReviewLike.objects.filter(review=review).count()

    return JsonResponse({
        "ok": True,
        "liked": liked,
        "like_count": like_count,
    })


@login_required
def review_likes_list(request, review_id):
    review = get_object_or_404(MovieReview, id=review_id)

    likes = review.likes.select_related("user").order_by("-created_at")

    return render(
        request,
        "movies/likes_modal.html",
        {"likes": likes}
    )



def person_detail(request, person_id):

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



@login_required
def comments_page(request, review_id):
    review = get_object_or_404(
        MovieReview.objects.select_related("movie", "user").prefetch_related("likes"),
        id=review_id
    )

    review.like_count = review.likes.count()
    review.is_liked = review.likes.filter(user=request.user).exists()
    review.comment_count = ReviewComment.objects.filter(review=review).count()
    text = (review.review_text or "").strip()
    review.show_more = (len(text) > 150) or (len(text.splitlines()) > 3)


    parent_comments = ReviewComment.objects.filter(
        review=review,
        parent__isnull=True
    ).select_related("user").prefetch_related(
        Prefetch(
            "replies",
            queryset=ReviewComment.objects.select_related("user").order_by("created_at")
        )
    ).order_by("-created_at")

    total_count = ReviewComment.objects.filter(review=review).count()

    context = {
        "review": review,
        "movie": review.movie,
        "parent_comments": parent_comments,
        "total_count": total_count,
        "is_owner": review.user == request.user,
    }

    return render(request, "movies/comments_page.html", context)




@login_required
def add_comment_page(request, review_id):
    if request.method != "POST":
        return redirect("comments-page", review_id=review_id)

    review = get_object_or_404(MovieReview, id=review_id)
    text = request.POST.get("text", "").strip()

    if not text:
        messages.error(request, "Comment cannot be empty")
        return redirect("comments-page", review_id=review_id)

    if len(text) > 500:
        messages.error(request, "Comment too long")
        return redirect("comments-page", review_id=review_id)

    ReviewComment.objects.create(
        user=request.user,
        review=review,
        text=text
    )

    messages.success(request, "Comment added")
    return redirect("comments-page", review_id=review_id)


@login_required
def reply_comment_page(request, comment_id):
    parent = get_object_or_404(ReviewComment, id=comment_id)

    if request.method != "POST":
        return redirect("comments-page", review_id=parent.review_id)

    if parent.parent_id is not None:
        messages.error(request, "Only 1 level reply allowed")
        return redirect("comments-page", review_id=parent.review_id)

    text = request.POST.get("text", "").strip()

    if not text:
        messages.error(request, "Reply cannot be empty")
        return redirect("comments-page", review_id=parent.review_id)

    if len(text) > 500:
        messages.error(request, "Reply too long")
        return redirect("comments-page", review_id=parent.review_id)

    ReviewComment.objects.create(
        user=request.user,
        review=parent.review,
        parent=parent,
        text=text
    )

    messages.success(request, "Reply added")
    return redirect("comments-page", review_id=parent.review_id)



@login_required
def delete_comment_page(request, comment_id):
    comment = get_object_or_404(
        ReviewComment.objects.select_related("review__user"),
        id=comment_id
    )

    if request.method != "POST":
        return redirect("comments-page", review_id=comment.review_id)

    is_comment_owner = (comment.user == request.user)
    is_review_owner = (comment.review.user == request.user)

    if not (is_comment_owner or is_review_owner):
        messages.error(request, "Not allowed")
        return redirect("comments-page", review_id=comment.review_id)

    review_id = comment.review_id
    comment.delete()

    messages.success(request, "Comment deleted")
    return redirect("comments-page", review_id=review_id)




@login_required
def hype_vote_movie(request, movie_id):
    if request.method != "POST":
        return redirect("movie-detail", movie_id=movie_id)

    movie = get_object_or_404(Movie, id=movie_id)

    if movie.is_released:
        messages.error(request, "Hype voting is only for upcoming movies.")
        return redirect("movie-detail", movie_id=movie_id)

    vote = request.POST.get("vote", "").strip().lower()

    allowed = {"excited", "not_excited", "remove"}
    if vote not in allowed:
        messages.error(request, "Invalid hype vote option.")
        return redirect("movie-detail", movie_id=movie_id)

    if vote == "remove":
        MovieHypeVote.objects.filter(user=request.user, movie=movie).delete()
        messages.success(request, "Hype vote removed.")
        return redirect("movie-detail", movie_id=movie_id)

    MovieHypeVote.objects.update_or_create(
        user=request.user,
        movie=movie,
        defaults={"vote": vote},
    )

    messages.success(request, "Hype vote saved.")
    return redirect("movie-detail", movie_id=movie_id)
