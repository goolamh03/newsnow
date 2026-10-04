"""Application configuration for the NewsNow application.

This module defines the Django application configuration for the
NewsNow app and ensures that signal handlers are registered when
the application starts.

The configuration is responsible for loading model signal
registrations used throughout the application.
"""

from django.apps import AppConfig


class NewsConfig(AppConfig):
    """Configure the NewsNow Django application.

    Defines application metadata and performs startup
    initialization tasks, including registration of
    model signal handlers.

    :ivar str default_auto_field:
        Default type for automatically generated primary keys.

    :ivar str name:
        Django application label.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "news"

    def ready(self):
        """Register application signal handlers.

        Imports the application's signal module when Django
        finishes loading installed applications. Importing the
        module ensures that all signal receivers are registered
        before the application begins processing requests.

        :return: None
        :rtype: None"""
        import news.signals  # noqa: F401
