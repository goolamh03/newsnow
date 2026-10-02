"""API views for the NewsNow application.

Provides REST API endpoints for managing articles, retrieving
subscribed content, approving articles, and receiving approved
article webhook notifications.
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

    Provides authenticated users with access to view approved
    articles and create new articles based on role permissions.
    """

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated, ArticleRolePermission]

    def get_queryset(self):
        """Return approved articles with related author and publisher data."""
        return Article.objects.filter(
            approved=True).select_related("author", "publisher")


class ArticleDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific article.

    Provides authenticated users with access to article details
    while enforcing role-based permissions.
    """

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated, ArticleRolePermission]

    def get_queryset(self):
        """Return articles with related author and publisher data."""
        return Article.objects.select_related("author", "publisher")


class SubscribedArticlesAPI(generics.ListAPIView):
    """List articles from subscribed publishers and journalists.

    Returns approved articles published by publishers or authors
    followed by the authenticated user.
    """

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return approved articles matching user subscriptions."""
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

    Validates and stores incoming approval data from external
    systems without requiring authentication.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Create an approved article log from webhook data."""
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

    Allows editors to mark an article as approved and make it
    available through article listing endpoints.
    """

    permission_classes = [IsEditor]

    def post(self, request, pk):
        """Approve the specified article and return a success response."""
        article = Article.objects.get(pk=pk)

        article.approved = True
        article.save()

        return Response(
            {"message": "Article approved."},
            status=status.HTTP_200_OK,
        )
