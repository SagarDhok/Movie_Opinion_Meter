from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from datetime import date, timedelta
from movies.models import Cast, Crew, Person
from movies.models import Movie, MovieReview, AIRequestLog
from .serializers import (
    MovieListSerializer,
    MovieDetailSerializer,
    ReviewSerializer,
    ReviewCreateSerializer,
    CastSerializer, CrewSerializer, PersonSerializer
)

from movies.services.ai_service import (
    ai_rewrite_review,
    ai_extract_pros_cons,
    clean_text,
)


# --------------------
# MOVIES
# --------------------

class MovieListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        search = request.GET.get("search", "").strip()
        genre = request.GET.get("genre", "").strip()
        status = request.GET.get("status", "").strip()
        today = date.today()

        qs = Movie.objects.prefetch_related("categories")

        if search:
            qs = qs.filter(title__icontains=search)

        if genre:
            qs = qs.filter(categories__id=genre)

        if status == "released":
            qs = qs.filter(release_date__isnull=False, release_date__lte=today)
        elif status == "upcoming":
            qs = qs.filter(Q(release_date__isnull=True) | Q(release_date__gt=today))

        qs = qs.distinct().order_by("-release_date")

        serializer = MovieListSerializer(qs, many=True)
        return Response(serializer.data)


class MovieDetailAPIView(RetrieveAPIView):
    queryset = Movie.objects.prefetch_related("categories")
    serializer_class = MovieDetailSerializer
    permission_classes = [AllowAny]





class MovieCastAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, movie_id):
        cast_qs = (
            Cast.objects
            .filter(movie_id=movie_id)
            .select_related("person")
            .order_by("id")
        )

        serializer = CastSerializer(cast_qs, many=True)
        return Response(serializer.data)


class MovieCrewAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, movie_id):
        crew_qs = (
            Crew.objects
            .filter(movie_id=movie_id)
            .select_related("person")
            .order_by("job")
        )

        serializer = CrewSerializer(crew_qs, many=True)
        return Response(serializer.data)


class PersonDetailAPIView(RetrieveAPIView):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [AllowAny]



# --------------------
# REVIEWS
# --------------------

class MovieReviewsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, movie_id):
        reviews = (
            MovieReview.objects
            .filter(movie_id=movie_id)
            .select_related("user")
            .order_by("-created_at")
        )

        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class ReviewCreateUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, movie_id):
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        MovieReview.objects.update_or_create(
            user=request.user,
            movie_id=movie_id,
            defaults=serializer.validated_data,
        )

        return Response({"message": "Review saved successfully"})


# --------------------
# AI HELPERS
# --------------------

def user_ai_limit_exceeded(user, action, minutes=10, limit=10):
    since = timezone.now() - timedelta(minutes=minutes)
    count = AIRequestLog.objects.filter(
        user=user,
        action=action,
        created_at__gte=since,
    ).count()
    return count >= limit


class AIRewriteReviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, movie_id):
        text = clean_text(request.data.get("text", ""))
        mode = request.data.get("mode", "rewrite")

        allowed_modes = {
            "rewrite",
            "shorten",
            "funny",
            "roast",
            "professional",
            "hype",
            "savage_1star",
        }

        if mode not in allowed_modes:
            return Response({"error": "Invalid mode"}, status=400)

        if user_ai_limit_exceeded(request.user, mode):
            return Response({"error": "Rate limit exceeded"}, status=429)

        movie = Movie.objects.filter(id=movie_id).first()

        log = AIRequestLog.objects.create(
            user=request.user,
            movie=movie,
            action=mode,
            input_text=text,
            success=False,
        )

        try:
            output = ai_rewrite_review(
                text=text,
                mode=mode,
                movie_title=movie.title if movie else "",
                movie_overview=movie.overview if movie else "",
            )

            log.output_text = output
            log.success = True
            log.save()

            return Response({"result": output})

        except Exception as e:
            log.error_message = str(e)[:255]
            log.save()
            return Response({"error": "AI failed"}, status=500)


class AIProsConsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, movie_id):
        text = clean_text(request.data.get("text", ""))

        if not text:
            return Response({"error": "Text required"}, status=400)

        if user_ai_limit_exceeded(request.user, "pros_cons"):
            return Response({"error": "Rate limit exceeded"}, status=429)

        movie = Movie.objects.filter(id=movie_id).first()

        log = AIRequestLog.objects.create(
            user=request.user,
            movie=movie,
            action="pros_cons",
            input_text=text,
            success=False,
        )

        try:
            data = ai_extract_pros_cons(text)

            log.output_text = f"Pros: {data['pros']} | Cons: {data['cons']}"
            log.success = True
            log.save()

            return Response({
                "pros": data["pros"],
                "cons": data["cons"],
            })

        except Exception:
            log.error_message = "AI failed"
            log.save()
            return Response({"error": "AI failed"}, status=500)
