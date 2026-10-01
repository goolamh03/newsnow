"""API views for the NewsNow application.

This module provides REST API endpoints for managing articles,
retrieving subscribed content, approving articles, and processing
approved article webhook notifications.

The API supports authenticated access for article management,
role-based permissions, editorial approval workflows, and
integration with external systems through webhook endpoints.
"""

from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Article
from .permissions import ArticleRolePermission
from .permissions import IsEditor
from .serializers import ArticleSerializer, ApprovedArticleLogSerializer


class ArticleListCreateAPI(generics.ListCreateAPIView):
    """List approved articles and create new articles.

    Authenticated users may retrieve approved articles and create
    new articles subject to role-based permissions.

    :ivar serializer_class:
        Serializer used for article instances.
    :ivar permission_classes:
        Permissions required to access the endpoint.
    """

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated, ArticleRolePermission]

    def get_queryset(self):
        """Return approved articles with related author and publisher data.

        Optimizes database access using ``select_related`` for
        associated author and publisher records.

        :return: QuerySet containing approved articles.
        :rtype: QuerySet"""
        return Article.objects.filter(
            approved=True).select_related("author", "publisher")


class ArticleDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific article.

    Provides authenticated users with access to individual article
    records while enforcing role-based access control.

    :ivar serializer_class:
        Serializer used for article instances.
    :ivar permission_classes:
        Permissions required to access the endpoint.
    """

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated, ArticleRolePermission]

    def get_queryset(self):
        """Return articles with related author and publisher data.

        Optimizes database access by loading related author and
        publisher records in a single query.

        :return: QuerySet containing articles.
        :rtype: QuerySet"""
        return Article.objects.select_related("author", "publisher")


class SubscribedArticlesAPI(generics.ListAPIView):
    """List articles from subscribed publishers and journalists.

    Returns approved articles published by publishers or authors
    followed by the authenticated user.

    :ivar serializer_class:
        Serializer used for article instances.
    :ivar permission_classes:
        Permissions required to access the endpoint.
    """

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return approved articles matching user subscriptions.

        Retrieves approved articles authored by subscribed
        journalists or published by subscribed publishers.

        :return: Filtered queryset of subscribed articles.
        :rtype: QuerySet"""
        user = self.request.user
        return (
            Article.objects.filter(approved=True)
            .filter(
                Q(publisher__in=user.subscribed_publishers.all())
                | Q(author__in=user.subscribed_journalists.all())
            )
            .distinct()
            .select_related("author", "publisher")
        )


class ApprovedArticleWebhookAPI(APIView):
    """Receive approved article webhook notifications.

    Validates and stores incoming approved article data received
    from external systems. Authentication is not required.

    :ivar permission_classes:
        Permissions required to access the endpoint.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Create an approved article log from webhook data.

        Validates the submitted payload and stores the resulting
        approval log record.

        :param request: Incoming HTTP request containing webhook data.
        :type request: HttpRequest

        :return: Serialized approval log data.
        :rtype: Response

        :raises ValidationError:
            If submitted webhook data is invalid."""
        serializer = ApprovedArticleLogSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class ArticleApprovalAPIView(APIView):
    """Approve an article.

    Allows users with editor permissions to mark an article as
    approved and make it available through article listing endpoints.

    :ivar permission_classes:
        Permissions required to access the endpoint.
    """

    permission_classes = [IsEditor]

    def post(self, request, pk):
        """Approve the specified article.

        Updates the article approval status and returns a
        confirmation response.

        :param request: Incoming HTTP request.
        :type request: HttpRequest

        :param pk: Primary key of the article to approve.
        :type pk: int

        :return: Confirmation response indicating success.
        :rtype: Response"""
        article = Article.objects.get(pk=pk)

        article.approved = True
        article.save()

        return Response(
            {"message": "Article approved."},
            status=status.HTTP_200_OK,
        )
