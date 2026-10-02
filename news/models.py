"""Data models for the NewsNow application.

Defines publishers, users, articles, newsletters, and article
approval logs used throughout the application.
"""

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class Publisher(models.Model):
    """Represent a news publisher."""

    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    editors = models.ManyToManyField(
        "User",
        related_name="edited_publishers",
        blank=True,
        limit_choices_to={"role": "EDITOR"},
    )
    journalists = models.ManyToManyField(
        "User",
        related_name="publisher_memberships",
        blank=True,
        limit_choices_to={"role": "JOURNALIST"},
    )

    def __str__(self):
        """Return the publisher name."""
        return self.name


class User(AbstractUser):
    """Represent a NewsNow user."""

    class Role(models.TextChoices):
        """Define available NewsNow roles."""

        READER = "READER", "Reader"
        EDITOR = "EDITOR", "Editor"
        JOURNALIST = "JOURNALIST", "Journalist"

    role = models.CharField(
        max_length=12,
        choices=Role.choices,
        default=Role.READER,
    )

    subscribed_publishers = models.ManyToManyField(
        Publisher,
        blank=True,
        related_name="subscribers",
    )

    subscribed_journalists = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="journalist_subscribers",
        limit_choices_to={"role": "JOURNALIST"},
    )

    def clean(self):
        """Validate user data."""
        super().clean()

    def save(self, *args, **kwargs):
        """
        Save the user and enforce role-specific relationships.

        ManyToMany fields cannot be assigned None in Django.
        Therefore incompatible relationships are cleared,
        which is the equivalent of having no value.
        """
        super().save(*args, **kwargs)

        if self.role != self.Role.READER:
            self.subscribed_publishers.clear()
            self.subscribed_journalists.clear()

        if self.role == self.Role.READER:
            self.publisher_memberships.clear()
            self.edited_publishers.clear()


class Article(models.Model):
    """Represent a news article."""

    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="articles",
        limit_choices_to={"role": "JOURNALIST"},
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    thumbnail = models.ImageField(
        upload_to="articles/",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    approval_notified = models.BooleanField(default=False)

    class Meta:
        """Configure article ordering."""

        ordering = ["-created_at"]

    def clean(self):
        """Validate article author and publisher relationships."""

        super().clean()

        if not self.author_id:
            return

        if self.author.role != User.Role.JOURNALIST:
            raise ValidationError(
                "Article author must be a journalist."
            )

        if (
            self.publisher_id
            and not self.publisher.journalists.filter(
                pk=self.author_id
            ).exists()
        ):
            raise ValidationError(
                "Author must belong to the selected publisher."
            )

    def __str__(self):
        """Return the article title."""
        return self.title


class Newsletter(models.Model):
    """Represent a collection of news articles."""

    title = models.CharField(max_length=200)
    description = models.TextField()
    thumbnail = models.ImageField(
        upload_to="newsletters/",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="newsletters",
        limit_choices_to={"role": "JOURNALIST"},
    )
    articles = models.ManyToManyField(Article, related_name="newsletters", blank=True)

    class Meta:
        """Configure newsletter model metadata."""

        ordering = ["-created_at"]

    def __str__(self):
        """Return the newsletter title."""
        return self.title


class ApprovedArticleLog(models.Model):
    """Store webhook data for approved articles."""

    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="approval_logs"
    )
