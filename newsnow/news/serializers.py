"""Serializers for the NewsNow application.

Provides serializers for users, publishers, articles,
newsletters, and approved article logs used by the REST API.
"""

from rest_framework import serializers
from .models import Article, Newsletter, Publisher, User, ApprovedArticleLog


class UserSerializer(serializers.ModelSerializer):
    """Serialize user information for API responses."""

    class Meta:
        """Configure the user serializer."""

        model = User
        fields = ("id", "username", "role")


class PublisherSerializer(serializers.ModelSerializer):
    """Serialize publisher information for API responses."""

    class Meta:
        """Configure the publisher serializer."""

        model = Publisher
        fields = ("id", "name", "description")


class ArticleSerializer(serializers.ModelSerializer):
    """Serialize article data for API requests and responses."""

    author = UserSerializer(read_only=True)
    publisher_detail = PublisherSerializer(source="publisher", read_only=True)

    class Meta:
        """Configure the article serializer."""

        model = Article
        fields = (
            "id",
            "title",
            "content",
            "author",
            "publisher",
            "publisher_detail",
            "created_at",
            "approved",
        )
        read_only_fields = ("approved",)

    def create(self, validated_data):
        """Create an article using the authenticated user as author."""
        return Article.objects.create(
            author=self.context["request"].user, **validated_data)


class NewsletterSerializer(serializers.ModelSerializer):
    """Serialize newsletter data for API requests and responses."""

    class Meta:
        """Configure the newsletter serializer."""

        model = Newsletter
        fields = (
            "id", "title", "description", "created_at", "author", "articles")
        read_only_fields = ("author",)


class ApprovedArticleLogSerializer(serializers.ModelSerializer):
    """Serialize approved article log records."""

    class Meta:
        """Configure the approved article log serializer."""

        model = ApprovedArticleLog
        fields = ("id", "article", "logged_at", "payload")
