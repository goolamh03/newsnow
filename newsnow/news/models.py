"""Data models for the NewsNow application.

This module defines the core data structures used throughout the
application, including publishers, users, articles, newsletters,
and approved article logs.

The models implement role-based user management, article approval
workflows, publisher membership validation, and newsletter
distribution functionality.
"""

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class Publisher(models.Model):
    """Represent a news publisher.

    Stores publisher information and maintains relationships
    with editors and journalists responsible for creating
    and managing content.

    :ivar str name:
        Unique publisher name.

    :ivar str description:
        Description of the publisher.

    :ivar editors:
        Editors assigned to the publisher.

    :ivar journalists:
        Journalists assigned to the publisher."""

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
        """Return the publisher name.

        :return: Publisher name.
        :rtype: str"""
        return self.name


class User(AbstractUser):
    """Represent a NewsNow user.

    Extends Django's built-in user model with role-based
    functionality and subscription relationships.

    Users may be readers, journalists, or editors.

    :ivar str role:
        User role within the NewsNow platform.

    :ivar subscribed_publishers:
        Publishers followed by the user.

    :ivar subscribed_journalists:
        Journalists followed by the user."""

    class Role(models.TextChoices):
        """Define available NewsNow user roles.

        :cvar str READER:
            Reader role.

        :cvar str EDITOR:
            Editor role.

        :cvar str JOURNALIST:
            Journalist role."""

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
        """Validate user data.

        Executes model-level validation before saving.

        :return: None
        :rtype: None"""
        super().clean()

    def save(self, *args, **kwargs):
        """
        Save the user and enforce role-specific relationships.

        Readers may subscribe to publishers and journalists.
        Journalists and editors cannot maintain subscriber
        relationships. Incompatible relationships are removed
        automatically after saving.

        :param args:
            Positional arguments passed to the parent method.

        :param kwargs:
            Keyword arguments passed to the parent method.
        """
        super().save(*args, **kwargs)

        if self.role != self.Role.READER:
            self.subscribed_publishers.clear()
            self.subscribed_journalists.clear()

        if self.role == self.Role.READER:
            self.publisher_memberships.clear()
            self.edited_publishers.clear()


class Article(models.Model):
    """Represent a news article.

    Stores article content created by journalists and
    optionally associated with a publisher.

    Articles require editorial approval before becoming
    publicly available.

    :ivar str title:
        Article title.

    :ivar str content:
        Article content.

    :ivar author:
        Journalist who authored the article.

    :ivar publisher:
        Publisher associated with the article.

    :ivar thumbnail:
        Optional article thumbnail image.

    :ivar created_at:
        Timestamp indicating when the article was created.

    :ivar bool approved:
        Indicates whether the article has been approved.

    :ivar bool approval_notified:
        Indicates whether approval notifications have been sent."""

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
        """Configure article model metadata.

        :ivar list ordering:
            Default ordering by creation date in descending order."""

        ordering = ["-created_at"]

    def clean(self):
        """Validate article relationships.

        Ensures the article author is a journalist and,
        when a publisher is specified, verifies that the
        author belongs to that publisher.

        :return: None
        :rtype: None

        :raises ValidationError:
            If the author is not a journalist.

        :raises ValidationError:
            If the author does not belong to the selected publisher."""

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
        """Return the article title.

        :return: Article title.
        :rtype: str"""
        return self.title


class Newsletter(models.Model):
    """Represent a newsletter.

    A newsletter is a collection of approved articles
    compiled for distribution to readers.

    :ivar str title:
        Newsletter title.

    :ivar str description:
        Newsletter description.

    :ivar thumbnail:
        Optional newsletter thumbnail image.

    :ivar created_at:
        Newsletter creation timestamp.

    :ivar author:
        Journalist who created the newsletter.

    :ivar articles:
        Articles included in the newsletter."""

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
        """Configure newsletter model metadata.

        :ivar list ordering:
            Default ordering by creation date in descending order."""

        ordering = ["-created_at"]

    def __str__(self):
        """Return the newsletter title.

        :return: Newsletter title.
        :rtype: str"""
        return self.title


class ApprovedArticleLog(models.Model):
    """Store approval notifications for articles.

    Records webhook data associated with article approvals
    received from external services.

    :ivar article:
        Approved article associated with the log entry."""

    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="approval_logs"
    )
