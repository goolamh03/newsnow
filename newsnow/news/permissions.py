"""Custom permission classes for the NewsNow application.

This module provides role-based access control for API endpoints
used to manage articles and editorial approval workflows.

Permissions determine which users may view, create, update,
delete, or approve articles based on their assigned role.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import User


class ArticleRolePermission(BasePermission):
    """Control access to article resources based on user roles.

    Readers may view approved articles, journalists may create
    and manage their own articles, and editors have unrestricted
    access to article management operations.
    """

    def has_permission(self, request, view):
        """Determine whether the user has permission to access the view.

        Read operations are available to all users. Article creation
        is restricted to journalists. Update and delete operations
        are limited to journalists and editors.

        :param request: Incoming HTTP request.
        :type request: HttpRequest

        :param view: Current API view.
        :type view: APIView

        :return: ``True`` if the user has view-level permission,
                 otherwise ``False``.
        :rtype: bool"""
        if request.method in SAFE_METHODS:
            return True

        if request.method == "POST":
            return request.user.role == User.Role.JOURNALIST

        return request.user.role in (
            User.Role.EDITOR,
            User.Role.JOURNALIST,
        )

    def has_object_permission(self, request, view, obj):
        """Determine whether the user can access a specific article.

        Readers can access only approved articles. Editors have
        unrestricted access. Journalists may modify only articles
        that they authored.

        :param request: Incoming HTTP request.
        :type request: HttpRequest

        :param view: Current API view.
        :type view: APIView

        :param obj: Article instance being accessed.
        :type obj: Article

        :return: ``True`` if access is permitted,
                 otherwise ``False``.
        :rtype: bool"""
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
    """Restrict access to editor users.

    Grants access only to authenticated users whose role
    is set to ``EDITOR``."""

    def has_permission(self, request, view):
        """Determine whether the authenticated user is an editor.

        :param request: Incoming HTTP request.
        :type request: HttpRequest

        :param view: Current API view.
        :type view: APIView

        :return: ``True`` if the authenticated user is an editor,
                 otherwise ``False``.
        :rtype: bool"""
        return bool(
            request.user and request.user.is_authenticated
            and request.user.role == User.Role.EDITOR
        )
