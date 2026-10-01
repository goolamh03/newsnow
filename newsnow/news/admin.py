"""Admin site configuration for the NewsNow application.

This module registers and customizes the Django administration
interface for users, publishers, articles, newsletters, and
article approval logs.

The custom user administration configuration extends Django's
built-in ``UserAdmin`` to support NewsNow-specific user roles
and subscription relationships.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    ApprovedArticleLog,
    Article,
    Newsletter,
    Publisher,
    User,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Customize the Django admin interface for NewsNow users.

    Extends Django's built-in ``UserAdmin`` by adding NewsNow-specific
    fields to the user administration screen, including user roles,
    publisher subscriptions, and journalist subscriptions.

    :ivar tuple fieldsets:
        Additional fieldsets displayed in the Django admin interface.
    """

    fieldsets = UserAdmin.fieldsets + (
        (
            "NewsNow",
            {
                "fields": (
                    "role",
                    "subscribed_publishers",
                    "subscribed_journalists",
                ),
            },
        ),
    )


admin.site.register(Publisher)
admin.site.register(Article)
admin.site.register(Newsletter)
admin.site.register(ApprovedArticleLog)
