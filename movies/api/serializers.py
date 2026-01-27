from rest_framework import serializers
from movies.models import Movie, MovieReview, Genre


class MovieListSerializer(serializers.ModelSerializer):
    genres = serializers.StringRelatedField(many=True, source="categories")

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "is_released",
            "release_date",
            "genres",
        ]


class MovieDetailSerializer(serializers.ModelSerializer):
    genres = serializers.StringRelatedField(many=True, source="categories")

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "overview",
            "is_released",
            "release_date",
            "genres",
        ]


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name")
    like_count = serializers.IntegerField()
    comment_count = serializers.IntegerField()
    user_vote = serializers.CharField(allow_null=True)

    class Meta:
        model = MovieReview
        fields = [
            "id",
            "user_name",
            "rating",
            "review_text",
            "like_count",
            "comment_count",
            "user_vote",
            "created_at",
        ]
