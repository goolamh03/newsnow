"""Admin site configuration for the NewsNow application.

Registers and customizes the admin interface for users, publishers,
articles, newsletters, and article approval logs.
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
    """Custom admin configuration for NewsNow users.

    Extends Django's built-in UserAdmin to include NewsNow-specific
    fields such as user roles, subscribed publishers, and subscribed
    journalists.
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
