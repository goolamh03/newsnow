"""Form definitions for the NewsNow application.

Provides forms for article management, newsletter creation,
user registration, and user authentication.
"""

from django import forms
from .models import Article, Newsletter, Publisher, User
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)


class RegistrationForm(UserCreationForm):
    """Register a NewsNow reader, journalist or editor."""

    role = forms.ChoiceField(
        choices=(
            (User.Role.READER, "Reader"),
            (User.Role.JOURNALIST, "Journalist"),
            (User.Role.EDITOR, "Editor"),
        )
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "role",
            "password1",
            "password2",
        )

    def clean_email(self):
        """Ensure email addresses are unique."""

        email = self.cleaned_data["email"]

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError(
                "An account with this email address already exists."
            )

        return email

    def __init__(self, *args, **kwargs):
        """Apply Bootstrap classes."""
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name == "role":
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"


class BootstrapAuthenticationForm(AuthenticationForm):
    """Apply Bootstrap styling to login form fields."""

    def __init__(self, *args, **kwargs):
        """Apply Bootstrap classes."""
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class ArticleForm(forms.ModelForm):
    """Create or update an article."""

    class Meta:
        """Configure article form fields."""

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
    """Create or update a newsletter."""

    class Meta:
        """Configure newsletter form fields."""

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
        """Limit newsletter articles to accessible approved articles."""
        super().__init__(*args, **kwargs)

        if author:
            self.fields["articles"].queryset = (
                Article.objects.filter(
                    approved=True,
                )
            )


class PublisherForm(forms.ModelForm):
    """Create or update a publisher."""

    class Meta:
        """Configure publisher form fields."""

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
