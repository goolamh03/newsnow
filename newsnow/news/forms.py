"""Form definitions for the NewsNow application.

This module provides forms for article management, newsletter creation,
publisher management, user registration, and user authentication.

The forms include Bootstrap styling and validation rules specific to
the NewsNow platform.
"""

from django import forms
from .models import Article, Newsletter, Publisher, User
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)


class RegistrationForm(UserCreationForm):
    """Register a NewsNow user.

    Extends Django's ``UserCreationForm`` to support NewsNow user roles
    including readers, journalists, and editors. The form also validates
    email uniqueness before creating a user account.

    :ivar ChoiceField role:
        User role selection field."""

    role = forms.ChoiceField(
        choices=(
            (User.Role.READER, "Reader"),
            (User.Role.JOURNALIST, "Journalist"),
            (User.Role.EDITOR, "Editor"),
        )
    )

    class Meta:
        """Configure registration form fields.

        :ivar User model:
            The user model associated with the form.
        :ivar tuple fields:
            Fields displayed during user registration.
        """
        model = User
        fields = (
            "username",
            "email",
            "role",
            "password1",
            "password2",
        )

    def clean_email(self):
        """Validate that the supplied email address is unique.

        Checks whether another user account already exists with the same
        email address. A validation error is raised if a duplicate email
        is found.

        :raises ValidationError:
            If the email address is already registered.

        :return: Validated email address.
        :rtype: str"""

        email = self.cleaned_data["email"]

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError(
                "An account with this email address already exists."
            )

        return email

    def __init__(self, *args, **kwargs):
        """Apply Bootstrap styling to form fields.

        :param args:
            Positional arguments passed to the parent form.
        :param kwargs:
            Keyword arguments passed to the parent form."""
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name == "role":
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"


class BootstrapAuthenticationForm(AuthenticationForm):
    """Authenticate a NewsNow user.

    Extends Django's authentication form and applies Bootstrap
    styling to all login form fields."""

    def __init__(self, *args, **kwargs):
        """Apply Bootstrap styling to login form widgets.

        :param args:
            Positional arguments passed to the parent form.
        :param kwargs:
            Keyword arguments passed to the parent form."""
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class ArticleForm(forms.ModelForm):
    """Create or update an article.

    Provides validation and Bootstrap-styled widgets for
    article management."""

    class Meta:
        """Configure article form fields.

        :ivar model:
            Article model associated with the form.

        :ivar tuple fields:
            Fields displayed in the form.

        :ivar dict widgets:
            Custom widgets applied to form fields."""

        model = Article
        fields = (
            "title",
            "content",
            "publisher",
            "thumbnail",
        )
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 8,
                }
            ),
            "publisher": forms.Select(
                attrs={"class": "form-select"}
            ),
        }


class NewsletterForm(forms.ModelForm):
    """Create or update a newsletter.

    Allows editors to create newsletters and associate
    approved articles with them."""

    class Meta:
        """Configure newsletter form fields.

        :ivar model:
            Newsletter model associated with the form.

        :ivar tuple fields:
            Fields displayed in the form.

        :ivar dict widgets:
            Custom widgets applied to form fields."""

        model = Newsletter
        fields = (
            "title",
            "description",
            "articles",
            "thumbnail",
        )
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                }
            ),
            "articles": forms.SelectMultiple(
                attrs={
                    "class": "form-select",
                    "size": 8,
                }
            ),
        }

    def __init__(self, *args, author=None, **kwargs):
        """Restrict available articles to approved content.

        Filters the article selection list based on the
        supplied author.

        :param args:
            Positional arguments passed to the parent form.

        :param author:
            User whose accessible articles should be displayed.
        :type author: User or None

        :param kwargs:
            Keyword arguments passed to the parent form."""
        super().__init__(*args, **kwargs)

        if author:
            self.fields["articles"].queryset = (
                Article.objects.filter(
                    approved=True,
                )
            )


class PublisherForm(forms.ModelForm):
    """Create or update a publisher.

    Provides management of publisher information, assigned
    editors, and assigned journalists."""

    class Meta:
        """Configure publisher form fields.

        :ivar model:
            Publisher model associated with the form.

        :ivar tuple fields:
            Fields displayed in the form.

        :ivar dict widgets:
            Custom widgets applied to form fields."""

        model = Publisher
        fields = (
            "name",
            "description",
            "editors",
            "journalists",
        )
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                }
            ),
            "editors": forms.SelectMultiple(
                attrs={
                    "class": "form-select",
                    "size": 6,
                }
            ),
            "journalists": forms.SelectMultiple(
                attrs={
                    "class": "form-select",
                    "size": 6,
                }
            ),
        }
