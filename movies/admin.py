from django.contrib import admin
from .models import Movie, Genre

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
