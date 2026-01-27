from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q

from movies.models import (
    Movie, MovieReview, ReviewLike,
    MovieVote, Watchlist, MovieHypeVote
)
from .serializers import (
    MovieListSerializer,
    MovieDetailSerializer,
    ReviewSerializer
)



class MovieListAPI(APIView):
    def get(self, request):
        qs = Movie.objects.all().prefetch_related("categories")

        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(qs, request)

        serializer = MovieListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)




class MovieDetailAPI(APIView):
    def get(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)

        vote_counts = MovieVote.objects.filter(movie=movie).values("vote").annotate(
            count=Count("id")
        )

        vote_summary = {v["vote"]: v["count"] for v in vote_counts}

        data = MovieDetailSerializer(movie).data
        data["vote_summary"] = vote_summary

        if not movie.is_released:
            total = MovieHypeVote.objects.filter(movie=movie).count()
            excited = MovieHypeVote.objects.filter(movie=movie, vote="excited").count()
            data["hype_score"] = round((excited / total) * 100) if total else 0

        return Response(data)



class MovieReviewsAPI(APIView):
    def get(self, request, movie_id):
        sort = request.GET.get("sort", "liked")

        qs = (
            MovieReview.objects
            .filter(movie_id=movie_id)
            .select_related("user")
            .annotate(
                like_count=Count("likes"),
                comment_count=Count("comments"),
            )
        )

        if sort == "latest":
            qs = qs.order_by("-created_at")
        else:
            qs = qs.order_by("-like_count", "-created_at")

        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(qs, request)

        data = []
        for r in page:
            user_vote = MovieVote.objects.filter(
                movie_id=movie_id,
                user=r.user
            ).first()

            r.user_vote = user_vote.vote if user_vote else None
            data.append(r)

        serializer = ReviewSerializer(data, many=True)
        return paginator.get_paginated_response(serializer.data)



class ToggleReviewLikeAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):
        review = get_object_or_404(MovieReview, id=review_id)

        like = ReviewLike.objects.filter(
            user=request.user, review=review
        )

        if like.exists():
            like.delete()
            liked = False
        else:
            ReviewLike.objects.create(user=request.user, review=review)
            liked = True

        return Response({
            "liked": liked,
            "like_count": ReviewLike.objects.filter(review=review).count()
        })



class MovieVoteAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, movie_id):
        vote = request.data.get("vote")

        if vote == "remove":
            MovieVote.objects.filter(
                user=request.user,
                movie_id=movie_id
            ).delete()
            return Response({"vote": None})

        obj, _ = MovieVote.objects.update_or_create(
            user=request.user,
            movie_id=movie_id,
            defaults={"vote": vote}
        )

        return Response({"vote": obj.vote})



class MeAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "id": request.user.id,
            "name": request.user.get_full_name(),
            "review_count": MovieReview.objects.filter(user=request.user).count(),
            "watchlist_count": Watchlist.objects.filter(user=request.user).count(),
        })


class MyWatchlistAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            Watchlist.objects
            .filter(user=request.user)
            .select_related("movie")
            .annotate(
                excited=Count(
                    "movie__hype_votes",
                    filter=Q(movie__hype_votes__vote="excited")
                ),
                total=Count("movie__hype_votes"),
            )
        )

        data = []
        for w in qs:
            data.append({
                "movie_id": w.movie.id,
                "title": w.movie.title,
                "is_released": w.movie.is_released,
                "added_at": w.created_at,
                "hype": {
                    "excited": w.excited,
                    "total": w.total,
                }
            })

        return Response(data)



class ToggleWatchlistAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, movie_id):
        obj = Watchlist.objects.filter(
            user=request.user,
            movie_id=movie_id
        )

        if obj.exists():
            obj.delete()
            in_watchlist = False
        else:
            Watchlist.objects.create(
                user=request.user,
                movie_id=movie_id
            )
            in_watchlist = True

        return Response({"in_watchlist": in_watchlist})



