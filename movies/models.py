from django.db import models

# Create your models here.


class Genre(models.Model):
    name = models.CharField(max_length=100,unique=True,db_index=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    tmdb_id = models.PositiveIntegerField(unique=True,db_index=True, help_text="TMDB movie ID")
    title = models.CharField(max_length=255,db_index=True)
    poster_path = models.CharField(max_length=255,blank=True,null=True)
    release_date = models.DateField(blank=True,null=True,db_index=True)
    is_released = models.BooleanField(default=False,db_index=True)
    categories = models.ManyToManyField(Genre,related_name="movies")  
            # synce.py
            # movie.categories.set(
            #     [genre_map[g] for g in m.get("genre_ids", []) if g in genre_map]
            # )
             # [<Genre: Action>, <Genre: Drama>]

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


from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class MovieVote(models.Model):
    VOTE_CHOICES = [
        ("masterpiece", "Masterpiece"),
        ("good", "Good"),
        ("average", "Average"),
        ("bad", "Bad"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey("Movie", on_delete=models.CASCADE, related_name="votes")
    vote = models.CharField(max_length=20, choices=VOTE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "movie")  


class MovieReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey("Movie", on_delete=models.CASCADE, related_name="reviews")

    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        null=True,
        blank=True
    )
    review_text = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "movie")


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey("Movie", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "movie")
