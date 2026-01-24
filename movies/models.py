from django.db import models
from django.conf import settings
from django.core.validators import MaxLengthValidator
User = settings.AUTH_USER_MODEL


# Create your models here.


class Genre(models.Model):
    name = models.CharField(max_length=100,unique=True,db_index=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    tmdb_id = models.PositiveIntegerField(unique=True, db_index=True)
    title = models.CharField(max_length=255, db_index=True)
    overview = models.TextField(blank=True, null=True)
    poster_path = models.CharField(max_length=255, blank=True, null=True)

    release_date = models.DateField(blank=True, null=True, db_index=True)
    is_released = models.BooleanField(default=False, db_index=True)

    # 🔥 IMPORTANT
    is_big_release = models.BooleanField(default=False, db_index=True)

    categories = models.ManyToManyField(Genre, related_name="movies")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ["-release_date"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["release_date"]),
            models.Index(fields=["is_released"]),
        ]

    def __str__(self):
        return self.title
    
class Person(models.Model):
    tmdb_id = models.IntegerField(unique=True, db_index=True)

    name = models.CharField(max_length=255, db_index=True)
    biography = models.TextField(blank=True)

    profile_path = models.CharField(max_length=255, blank=True, null=True)
    known_for_department = models.CharField(max_length=100, blank=True)

    birthday = models.DateField(null=True, blank=True)
    place_of_birth = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name


    
class Cast(models.Model):
    movie = models.ForeignKey(Movie, related_name="cast", on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    character = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.person.name} as {self.character}"



class Crew(models.Model):
    movie = models.ForeignKey(Movie, related_name="crew", on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    job = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.person.name} ({self.job})"




class Watchlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="watchlist_items")
    movie = models.ForeignKey("Movie",on_delete=models.CASCADE,related_name="watchlisted_by" )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "movie")

    def __str__(self):
        return f"{self.user.email} → {self.movie.title}"

#!Not Inlcluded yet 

class MovieVote(models.Model):
    VOTE_CHOICES = [
        ("masterpiece", "Masterpiece"),
        ("good", "Good"),
        ("average", "Average"),
        ("bad", "Bad"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    movie = models.ForeignKey("Movie", on_delete=models.CASCADE, related_name="votes")
    vote = models.CharField(max_length=20, choices=VOTE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "movie")  

class MovieReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="reviews")

    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)]
    )
    review_text = models.TextField(
        validators=[MaxLengthValidator(1000)]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    contains_spoiler = models.BooleanField(default=False) 

    class Meta:
        unique_together = ("user", "movie")




class ReviewLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    review = models.ForeignKey(MovieReview, related_name="likes", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "review")

class ReviewComment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    review = models.ForeignKey(
        MovieReview,
        related_name="comments",
        on_delete=models.CASCADE
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="replies",
        on_delete=models.CASCADE
    )

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:40]
    
class CommentLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.ForeignKey(
        ReviewComment,
        related_name="likes",
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "comment")
