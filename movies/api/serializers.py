from rest_framework import serializers
from movies.models import (Movie,Genre,MovieReview,Cast, Crew, Person)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name"]


class MovieListSerializer(serializers.ModelSerializer):
    categories = GenreSerializer(many=True)

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "poster_path",
            "release_date",
            "is_released",
            "categories",
        ]


class MovieDetailSerializer(serializers.ModelSerializer):
    categories = GenreSerializer(many=True)
    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "overview",
            "poster_path",
            "release_date",
            "is_released",
            "categories",
        ]



class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = [
            "id",
            "name",
            "biography",
            "profile_path",
            "known_for_department",
            "birthday",
            "place_of_birth",
        ]


class CastSerializer(serializers.ModelSerializer):
    person = PersonSerializer()

    class Meta:
        model = Cast
        fields = [
            "id",
            "character",
            "person",
        ]


class CrewSerializer(serializers.ModelSerializer):
    person = PersonSerializer()
    class Meta:
        model = Crew
        fields = [
            "id",
            "job",
            "person",
        ]



class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    class Meta:
        model = MovieReview
        fields = [
            "id",
            "user",
            "rating",
            "review_text",
            "contains_spoiler",
            "created_at",
        ]


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieReview
        fields = ["rating", "review_text", "contains_spoiler"]
