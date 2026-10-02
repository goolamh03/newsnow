"""Application configuration for the NewsNow app.

Defines application settings and initializes signal handlers when
the application starts.
"""

from django.apps import AppConfig


class NewsConfig(AppConfig):
    """Configure the NewsNow application.

    Specifies application metadata and loads signal registrations
    during startup.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "news"

    def ready(self):
        """Import signal handlers when the application is ready."""
        import news.signals  # noqa: F401
