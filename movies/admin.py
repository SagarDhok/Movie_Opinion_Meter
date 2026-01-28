from django.contrib import admin
from django.contrib import admin
from .models import (
    Genre,
    Movie,
    Person,
    Cast,
    Crew,
    Watchlist,
    MovieVote,
    MovieReview,
    ReviewLike,
    ReviewComment,
    MovieHypeVote,
    AIRequestLog,
)


# Register your models here.


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "release_date", "is_released")
    list_filter = ("is_released", "release_date", "categories")
    search_fields = ("title",)
    filter_horizontal = ("categories",)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "known_for_department", "birthday")
    search_fields = ("name",)
    list_filter = ("known_for_department",)

@admin.register(Cast)
class CastAdmin(admin.ModelAdmin):
    list_display = ("movie", "person", "character")
    search_fields = ("person__name", "movie__title")
    raw_id_fields = ("movie", "person")


@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin):
    list_display = ("movie", "person", "job")
    search_fields = ("person__name", "movie__title", "job")
    raw_id_fields = ("movie", "person")





@admin.register(MovieReview)
class MovieReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "movie",
        "user",
        "rating",
        "contains_spoiler",
        "created_at",
    )
    list_filter = ("rating", "contains_spoiler", "created_at")
    search_fields = ("movie__title", "user__email", "review_text")
    raw_id_fields = ("user", "movie")
    readonly_fields = ("created_at",)




@admin.register(ReviewLike)
class ReviewLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "review", "created_at")
    raw_id_fields = ("user", "review")
    readonly_fields = ("created_at",)


@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "review", "parent", "created_at")
    search_fields = ("text", "user__email")
    raw_id_fields = ("user", "review", "parent")
    readonly_fields = ("created_at",)





@admin.register(MovieVote)
class MovieVoteAdmin(admin.ModelAdmin):
    list_display = ("id", "movie", "user", "vote", "created_at")
    list_filter = ("vote",)
    raw_id_fields = ("user", "movie")


@admin.register(MovieHypeVote)
class MovieHypeVoteAdmin(admin.ModelAdmin):
    list_display = ("id", "movie", "user", "vote", "created_at")
    list_filter = ("vote",)
    raw_id_fields = ("user", "movie")


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "movie", "created_at")
    raw_id_fields = ("user", "movie")
    readonly_fields = ("created_at",)





@admin.register(AIRequestLog)
class AIRequestLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "action",
        "success",
        "created_at",
    )
    list_filter = ("action", "success", "created_at")
    search_fields = ("input_text", "output_text", "user__email")
    readonly_fields = ("created_at",)



