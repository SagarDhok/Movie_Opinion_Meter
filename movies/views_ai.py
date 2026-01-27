from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from datetime import timedelta

from .models import Movie, AIRequestLog
from .services.ai_service import ai_rewrite_review, ai_extract_pros_cons, clean_text
import logging
logger = logging.getLogger(__name__)



def user_ai_limit_exceeded(user, action, minutes=10, limit=5):
    since = timezone.now() - timedelta(minutes=minutes)
    count = AIRequestLog.objects.filter(user=user, action=action, created_at__gte=since).count()
    return count >= limit


@login_required
def ai_review_assistant(request, movie_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Invalid method"}, status=405)

    movie = Movie.objects.filter(id=movie_id).first()

    text = clean_text(request.POST.get("text", ""))
    mode = request.POST.get("mode", "rewrite").strip()

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
        return JsonResponse({"ok": False, "error": "Invalid mode"}, status=400)


    if not text:
        if not movie or not movie.title:
            return JsonResponse({"ok": False, "error": "Movie context missing"}, status=400)
    

    if len(text) > 1000:
        return JsonResponse({"ok": False, "error": "Review too long"}, status=400)

    if user_ai_limit_exceeded(request.user, mode, minutes=10, limit=100):#developer mode now 
        return JsonResponse({"ok": False, "error": "Too many requests. Try later."}, status=429)

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
                movie_overview=movie.overview if movie and movie.overview else ""
                )


        log.output_text = output
        log.success = True
        log.save()

        logger.info(
            "AI review generated",
            extra={
                "user_id": request.user.id,
                "movie_id": movie.id if movie else None,
                "mode": mode,
            }
        )


        return JsonResponse({"ok": True, "result": output})

    except Exception as e:
        log.error_message = str(e)[:255]
        log.save()

        logger.error(
        "AI review failed",
        extra={
            "user_id": request.user.id,
            "movie_id": movie.id if movie else None,
            "mode": mode,
            "error": str(e),})
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
    


@login_required
def ai_pros_cons(request, movie_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Invalid method"}, status=405)

    movie = Movie.objects.filter(id=movie_id).first()

    text = clean_text(request.POST.get("text", ""))
    
   
    if not text:
      return JsonResponse({"ok": False, "error": "Review is empty"}, status=400)


    if len(text) < 10:
        return JsonResponse({"ok": False, "error": "Review too short"}, status=400)

    if len(text) > 1000:
        return JsonResponse({"ok": False, "error": "Review too long"}, status=400)

    if user_ai_limit_exceeded(request.user, "pros_cons", minutes=10, limit=100): #for developer mode now 

        return JsonResponse({"ok": False, "error": "Too many requests. Try later."}, status=429)

    log = AIRequestLog.objects.create(
        user=request.user,
        movie=movie,
        action="pros_cons",
        input_text=text,
        success=False,
    )

    try:
        data = ai_extract_pros_cons(text)
        log.output_text = f"Pros: {data.get('pros')} | Cons: {data.get('cons')}"
        log.success = True
        log.save()

        logger.info(
            "AI pros/cons generated",
            extra={
                "user_id": request.user.id,
                "movie_id": movie.id if movie else None,
            }
        )


        return JsonResponse({"ok": True, "pros": data["pros"], "cons": data["cons"]})

    except Exception as e:
        log.error_message = str(e)[:255]
        log.save()

        logger.error(
        "AI pros/cons failed",
        extra={
            "user_id": request.user.id,
            "movie_id": movie.id if movie else None,
            "error": str(e),
            }
        )

        return JsonResponse({"ok": False, "error": "AI failed"}, status=500)


from django.shortcuts import get_object_or_404
from .models import MovieReview

@login_required
def ai_pros_cons_review(request, review_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Invalid method"}, status=405)

    review = get_object_or_404(MovieReview.objects.select_related("movie"), id=review_id)

    text = clean_text(review.review_text or "")

  
    if not text:
      return JsonResponse({"ok": False, "error": "Review is empty"},status=400)

    if len(text) < 10:
        return JsonResponse({"ok": False, "error": "Write at least 10 characters"}, status=400)
    

    if user_ai_limit_exceeded(request.user, "pros_cons", minutes=10, limit=100):
        return JsonResponse({"ok": False, "error": "Too many requests. Try later."}, status=429)

    log = AIRequestLog.objects.create(
        user=request.user,
        movie=review.movie,
        action="pros_cons",
        input_text=text,
        success=False,
    )

    try:
        data = ai_extract_pros_cons(text)
        
        log.output_text = f"Pros: {data.get('pros')} | Cons: {data.get('cons')}"
        log.success = True
        log.save()

        logger.info(
            "AI pros/cons generated",
            extra={
                "user_id": request.user.id,
                "review_id": review.id,
                "movie_id": review.movie.id,
            }
        )

    


        return JsonResponse({"ok": True, "pros": data["pros"], "cons": data["cons"]})
    except Exception as e:
        log.error_message = str(e)[:255]
        log.save()

        logger.error(
            "AI pros/cons failed",
            extra={
                "user_id": request.user.id,
                "review_id": review.id,
                "movie_id": review.movie.id,
                "error": str(e),
            }
        )
        return JsonResponse({"ok": False, "error": "AI failed"}, status=500)
