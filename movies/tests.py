"""
movies/tests.py
20 INTERVIEW-READY HIGH-IMPACT TESTS
Consolidated to maximize coverage while staying around 35 total project tests.
"""

from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.db import IntegrityError, transaction
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from movies.models import (
    Genre, Movie, MovieVote, MovieHypeVote,
    MovieReview, ReviewLike, ReviewComment,
    Watchlist, AIRequestLog, Person, Cast, Crew,
)
from movies.forms import MovieReviewForm
from movies.services.ai_service import clean_text, build_prompt
from movies.utils import attach_hype_score
from movies.views_ai import user_ai_limit_exceeded


# ─── helpers ────────────────────────────────────────────────────
def make_user(email="test@example.com", verified=True):
    user = User.objects.create_user(
        email=email, password="StrongPass123!", first_name="Test", last_name="User"
    )
    user.is_email_verified = verified
    user.save()
    return user


def make_movie(title="Inception", released=True, tmdb_id=None):
    return Movie.objects.create(
        tmdb_id=tmdb_id or Movie.objects.count() + 1000,
        title=title,
        is_released=released,
        release_date=date.today() - timedelta(days=30) if released else date.today() + timedelta(days=30),
    )


class MoviesTestCase(TestCase):
    def setUp(self):
        self.user = make_user()
        self.movie = make_movie()
        self.client = Client()
        self.client.login(email="test@example.com", password="StrongPass123!")

    def test_movie_model_constraints_and_cascades(self):
        MovieVote.objects.create(user=self.user, movie=self.movie, vote="good")
        try:
            with transaction.atomic():
                MovieVote.objects.create(user=self.user, movie=self.movie, vote="bad")
            self.fail("Should have raised IntegrityError")
        except IntegrityError:
            pass
        
        MovieReview.objects.create(user=self.user, movie=self.movie, rating=4, review_text="Great film")
        try:
            with transaction.atomic():
                MovieReview.objects.create(user=self.user, movie=self.movie, rating=2, review_text="Changed mind")
            self.fail("Should have raised IntegrityError")
        except IntegrityError:
            pass
        
        Watchlist.objects.create(user=self.user, movie=self.movie)
        try:
            with transaction.atomic():
                Watchlist.objects.create(user=self.user, movie=self.movie)
            self.fail("Should have raised IntegrityError")
        except IntegrityError:
            pass

        self.movie.delete()
        self.assertEqual(MovieVote.objects.count(), 0)
        self.assertEqual(MovieReview.objects.count(), 0)
        self.assertEqual(Watchlist.objects.count(), 0)

    def test_ai_request_log_set_null(self):
        log = AIRequestLog.objects.create(user=self.user, movie=self.movie, action="rewrite", input_text="test")
        self.movie.delete()
        log.refresh_from_db()
        self.assertIsNone(log.movie)

    def test_models_str_representations(self):
        genre = Genre.objects.create(name="Action")
        person = Person.objects.create(tmdb_id=999, name="Leo")
        cast = Cast.objects.create(movie=self.movie, person=person, character="Cobb")
        crew = Crew.objects.create(movie=self.movie, person=person, job="Director")
        review = MovieReview.objects.create(user=self.user, movie=self.movie, rating=4, review_text="A"*60)
        comment = ReviewComment.objects.create(user=self.user, review=review, text="A"*60)

        self.assertEqual(str(self.movie), "Inception")
        self.assertEqual(str(genre), "Action")
        self.assertEqual(str(cast), "Leo as Cobb")
        self.assertEqual(str(crew), "Leo (Director)")
        self.assertEqual(len(str(comment)), 40)  # comment truncates
        self.assertEqual(str(self.user), "Test User")

    def test_vote_movie_actions(self):
        url = reverse("vote-movie", args=[self.movie.id])
        self.client.post(url, {"vote": "good"})
        self.assertEqual(MovieVote.objects.get(user=self.user, movie=self.movie).vote, "good")
        self.client.post(url, {"vote": "masterpiece"})
        self.assertEqual(MovieVote.objects.get(user=self.user, movie=self.movie).vote, "masterpiece")
        self.client.post(url, {"vote": "terrible"})
        self.assertEqual(MovieVote.objects.get(user=self.user, movie=self.movie).vote, "masterpiece")
        self.client.post(url, {"vote": "remove"})
        self.assertEqual(MovieVote.objects.count(), 0)

    def test_hype_vote_rules(self):
        unreleased_movie = make_movie("Upcoming", released=False)
        url_unreleased = reverse("hype-vote-movie", args=[unreleased_movie.id])
        url_released = reverse("hype-vote-movie", args=[self.movie.id])

        self.client.post(url_unreleased, {"vote": "excited"})
        self.assertTrue(MovieHypeVote.objects.filter(movie=unreleased_movie).exists())
        
        self.client.post(url_released, {"vote": "excited"})
        self.assertFalse(MovieHypeVote.objects.filter(movie=self.movie).exists())

    def test_toggle_watchlist_and_like(self):
        review = MovieReview.objects.create(user=self.user, movie=self.movie, rating=4, review_text="Nice")
        watch_url = reverse("toggle-watchlist", args=[self.movie.id])
        like_url = reverse("toggle-review-like", args=[review.id])

        self.client.post(watch_url)
        self.assertTrue(Watchlist.objects.filter(user=self.user).exists())
        resp = self.client.post(like_url)
        self.assertTrue(resp.json()["liked"])
        
        self.client.post(watch_url)
        self.assertFalse(Watchlist.objects.filter(user=self.user).exists())
        resp = self.client.post(like_url)
        self.assertFalse(resp.json()["liked"])

    def test_comment_system_rules(self):
        review = MovieReview.objects.create(user=self.user, movie=self.movie, rating=3, review_text="OK")
        add_url = reverse("add-comment-page", args=[review.id])

        self.client.post(add_url, {"text": "Top level"})
        parent = ReviewComment.objects.last()

        reply = ReviewComment.objects.create(user=self.user, review=review, parent=parent, text="Reply")
        reply_url = reverse("reply-comment-page", args=[reply.id])
        self.client.post(reply_url, {"text": "Deep reply"})
        
        self.assertEqual(ReviewComment.objects.count(), 2)

    def test_comment_deletion_ownership(self):
        owner = make_user("owner@x.com")
        commenter = make_user("commenter@x.com")
        stranger = make_user("stranger@x.com")
        review = MovieReview.objects.create(user=owner, movie=self.movie, rating=5, review_text="Amazing")
        comment = ReviewComment.objects.create(user=commenter, review=review, text="I agree")
        url = reverse("delete-comment-page", args=[comment.id])

        self.client.login(email="stranger@x.com", password="StrongPass123!")
        self.client.post(url)
        self.assertTrue(ReviewComment.objects.filter(id=comment.id).exists())

        self.client.login(email="owner@x.com", password="StrongPass123!")
        self.client.post(url)
        self.assertFalse(ReviewComment.objects.filter(id=comment.id).exists())

    def test_submit_and_delete_movie_review(self):
        url = reverse("submit-review", args=[self.movie.id])
        del_url = reverse("delete-review", args=[self.movie.id])
        
        self.client.post(url, {"rating": 4, "review_text": "First", "contains_spoiler": False})
        self.assertEqual(MovieReview.objects.count(), 1)
        self.client.post(url, {"rating": 5, "review_text": "Updated", "contains_spoiler": False})
        self.assertEqual(MovieReview.objects.get(user=self.user, movie=self.movie).rating, 5)
        self.client.post(del_url)
        self.assertEqual(MovieReview.objects.count(), 0)

    def test_public_views_access(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("movies-home")).status_code, 200)
        resp = self.client.get(reverse("movie-detail", args=[self.movie.id]))
        self.assertIn(resp.status_code, [200, 302])

    def test_protected_views_redirect(self):
        self.client.logout()
        resp = self.client.post(reverse("vote-movie", args=[self.movie.id]), {"vote": "good"})
        self.assertRedirects(resp, f"{reverse('login')}?next={reverse('vote-movie', args=[self.movie.id])}")

    def test_review_form_validation(self):
        form1 = MovieReviewForm(data={"rating": 6, "review_text": "   ", "contains_spoiler": False})
        self.assertFalse(form1.is_valid())
        self.assertIn("review_text", form1.errors)
        self.assertIn("rating", form1.errors)
        
        form2 = MovieReviewForm(data={"rating": 3, "review_text": "Good", "contains_spoiler": False})
        self.assertTrue(form2.is_valid())

    def test_movies_api_list_and_search(self):
        make_movie("The Matrix", tmdb_id=201)
        api_client = APIClient()
        resp = api_client.get("/api/movies/")
        self.assertEqual(len(resp.data), 2)

        resp2 = api_client.get("/api/movies/", {"search": "matrix"})
        self.assertEqual(len(resp2.data), 1)

    def test_review_api_auth_and_create(self):
        api_client = APIClient()
        url = f"/api/movies/{self.movie.id}/review/"
        data = {"rating": 5, "review_text": "Awesome!", "contains_spoiler": False}
        
        self.assertEqual(api_client.post(url, data).status_code, status.HTTP_401_UNAUTHORIZED)
        
        api_client.force_authenticate(user=self.user)
        self.assertEqual(api_client.post(url, data).status_code, status.HTTP_200_OK)
        self.assertTrue(MovieReview.objects.filter(user=self.user, movie=self.movie).exists())



    def test_ai_service_clean_and_prompt(self):
        self.assertEqual(clean_text("  spaces   here  "), "spaces here")
        self.assertEqual(clean_text(None), "")
        
        prompt = build_prompt("review", "funny", "Title")
        self.assertIn("funny", prompt)
        self.assertIn("Title", prompt)

    def test_ai_rate_limiting(self):
        for i in range(10):
            AIRequestLog.objects.create(user=self.user, movie=self.movie, action="rewrite", input_text="t")
        
        self.assertTrue(user_ai_limit_exceeded(self.user, "rewrite"))

        self.assertFalse(user_ai_limit_exceeded(self.user, "funny"))

    def test_ai_review_assistant_view(self):
        url = reverse("ai-review-assistant", args=[self.movie.id])
        self.assertEqual(self.client.post(url, {"text": "A", "mode": "hacker"}).status_code, 400)
        for _ in range(10):
            AIRequestLog.objects.create(user=self.user, movie=self.movie, action="rewrite", input_text="t")
        self.assertEqual(self.client.post(url, {"text": "A", "mode": "rewrite"}).status_code, 429)

    def test_attach_hype_score_util(self):
        obj = MagicMock()
        obj.excited_count = 50
        obj.total_hype_votes = 100
        result = attach_hype_score([obj])
        self.assertEqual(result[0].hype_score, 50)

    def test_home_status_and_coming_soon_use_release_date(self):
        stale_released = Movie.objects.create(
            tmdb_id=99901,
            title="Stale Released",
            is_released=False,
            release_date=date.today() - timedelta(days=10),
        )
        stale_upcoming = Movie.objects.create(
            tmdb_id=99902,
            title="Stale Upcoming",
            is_released=True,
            release_date=date.today() + timedelta(days=10),
        )

        released_resp = self.client.get(reverse("movies-home"), {"released": "released"})
        released_titles = {m.title for m in released_resp.context["movies"]}
        self.assertIn(stale_released.title, released_titles)
        self.assertNotIn(stale_upcoming.title, released_titles)

        upcoming_resp = self.client.get(reverse("movies-home"), {"released": "upcoming"})
        upcoming_titles = {m.title for m in upcoming_resp.context["movies"]}
        self.assertIn(stale_upcoming.title, upcoming_titles)
        self.assertNotIn(stale_released.title, upcoming_titles)

        home_resp = self.client.get(reverse("movies-home"))
        coming_soon_titles = {m.title for m in home_resp.context["coming_soon_movies"]}
        self.assertIn(stale_upcoming.title, coming_soon_titles)
        self.assertNotIn(stale_released.title, coming_soon_titles)
