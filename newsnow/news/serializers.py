"""Serializers for the NewsNow application.

This module provides serializers used by the REST API to convert
model instances into JSON representations and validate incoming
request data.

Serializers are provided for users, publishers, articles,
newsletters, and approved article log records.
"""

from rest_framework import serializers
from .models import Article, Newsletter, Publisher, User, ApprovedArticleLog


class UserSerializer(serializers.ModelSerializer):
    """Serialize user information.

    Provides a simplified representation of user data
    for API responses.

    :ivar Meta:
        Serializer configuration metadata."""

    class Meta:
        """Configure the user serializer.

        :ivar model:
            User model associated with the serializer.

        :ivar tuple fields:
            User fields exposed through the API."""

        model = User
        fields = ("id", "username", "role")


class PublisherSerializer(serializers.ModelSerializer):
    """Serialize publisher information.

    Provides publisher details for API responses.

    :ivar Meta:
        Serializer configuration metadata."""

    class Meta:
        """Configure the publisher serializer.

        :ivar model:
            Publisher model associated with the serializer.

        :ivar tuple fields:
            Publisher fields exposed through the API."""

        model = Publisher
        fields = ("id", "name", "description")


class ArticleSerializer(serializers.ModelSerializer):
    """Serialize article data.

    Supports conversion of article instances to and from
    JSON representations used by the REST API.

    Includes nested author and publisher details for
    read operations.

    :ivar author:
        Read-only serialized article author.

    :ivar publisher_detail:
        Read-only serialized publisher information."""

    author = UserSerializer(read_only=True)
    publisher_detail = PublisherSerializer(source="publisher", read_only=True)

    class Meta:
        """Configure the article serializer.

        :ivar model:
            Article model associated with the serializer.

        :ivar tuple fields:
            Fields exposed through the API.

        :ivar tuple read_only_fields:
            Fields that cannot be modified via the API."""

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
        """Create an article instance.

        The authenticated user is automatically assigned
        as the article author.

        :param dict validated_data:
            Validated serializer data.

        :return: Newly created article.
        :rtype: Article"""
        return Article.objects.create(
            author=self.context["request"].user, **validated_data)


class NewsletterSerializer(serializers.ModelSerializer):
    """Serialize newsletter data.

    Handles conversion of newsletter instances to and from
    JSON representations used by the REST API.

    :ivar Meta:
        Serializer configuration metadata."""

    class Meta:
        """Configure the newsletter serializer.

        :ivar model:
            Newsletter model associated with the serializer.

        :ivar tuple fields:
            Fields exposed through the API.

        :ivar tuple read_only_fields:
            Fields that cannot be modified via the API."""

        model = Newsletter
        fields = (
            "id", "title", "description", "created_at", "author", "articles")
        read_only_fields = ("author",)


class ApprovedArticleLogSerializer(serializers.ModelSerializer):
    """Serialize approved article log records.

    Used for creating and retrieving webhook approval
    log entries.

    :ivar Meta:
        Serializer configuration metadata."""

    class Meta:
        """Configure the approved article log serializer.

        :ivar model:
            ApprovedArticleLog model associated with
            the serializer.

        :ivar tuple fields:
            Log fields exposed through the API."""

        model = ApprovedArticleLog
        fields = ("id", "article", "logged_at", "payload")
