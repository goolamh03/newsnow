"""Custom permission classes for the NewsNow application.

Provides role-based access control for article management and
editor-only functionality within the API.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import User


class ArticleRolePermission(BasePermission):
    """Control article access based on user roles.

    Readers can view approved articles, journalists can create
    and manage their own articles, and editors have full access
    to article management.
    """

    def has_permission(self, request, view):
        """Determine whether the user has permission for the request."""
        if request.method in SAFE_METHODS:
            return True

        if request.method == "POST":
            return request.user.role == User.Role.JOURNALIST

        return request.user.role in (
            User.Role.EDITOR,
            User.Role.JOURNALIST,
        )

    def has_object_permission(self, request, view, obj):
        """Determine whether the user can access the specific article."""
        if request.method in SAFE_METHODS:
            return (
                obj.approved
                or request.user.role in (
                    User.Role.EDITOR,
                    User.Role.JOURNALIST,
                )
            )

        if request.user.role == User.Role.EDITOR:
            return True

        return (
            request.user.role == User.Role.JOURNALIST
            and obj.author_id == request.user.id
        )


class IsEditor(BasePermission):
    """Allow access only to editors."""

    def has_permission(self, request, view):
        """Determine whether the authenticated user is an editor."""
        return bool(
            request.user and request.user.is_authenticated
            and request.user.role == User.Role.EDITOR
        )
