"""Views for the NewsNow application.

Provides web-based functionality for viewing, creating, updating,
and approving articles, managing subscriptions, and registering
new users.
"""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ArticleForm,
    NewsletterForm,
    PublisherForm,
    RegistrationForm,
)
from .models import Article, Newsletter, Publisher, User
from django.core.exceptions import ValidationError


def article_list(request):
    """Display all approved articles."""
    articles = (
        Article.objects.filter(approved=True)
        .select_related("author", "publisher")
        .order_by("-created_at")
    )

    return render(
        request,
        "news/article_list.html",
        {"articles": articles},
    )


def article_detail(request, pk):
    """Display one approved article."""
    article = get_object_or_404(
        Article.objects.select_related(
            "author",
            "publisher",
        ),
        pk=pk,
        approved=True,
    )

    return render(
        request,
        "news/article_detail.html",
        {"article": article},
    )


def newsletter_list(request):
    """Display newsletters to all users."""
    newsletters = (
        Newsletter.objects.select_related("author")
        .prefetch_related("articles")
        .order_by("-created_at")
    )

    return render(
        request,
        "news/newsletter_list.html",
        {"newsletters": newsletters},
    )


def newsletter_detail(request, pk):
    """Display one newsletter."""
    newsletter = get_object_or_404(
        Newsletter.objects.select_related(
            "author"
        ).prefetch_related(
            "articles"
        ),
        pk=pk,
    )

    return render(
        request,
        "news/newsletter_detail.html",
        {"newsletter": newsletter},
    )


@login_required
def newsletter_create(request):
    """Allow journalists to create newsletters."""
    if request.user.role != User.Role.JOURNALIST:
        return HttpResponseForbidden(
            "Only journalists may create newsletters."
        )

    form = NewsletterForm(
        request.POST or None,
        author=request.user,
    )

    if form.is_valid():
        newsletter = form.save(commit=False)
        newsletter.author = request.user
        newsletter.save()
        form.save_m2m()

        messages.success(
            request,
            "Newsletter created successfully.",
        )

        return redirect(
            "newsletter-detail",
            pk=newsletter.pk,
        )

    return render(
        request,
        "news/newsletter_form.html",
        {
            "form": form,
            "heading": "Create Newsletter",
        },
    )


@login_required
def newsletter_update(request, pk):
    """Allow owning journalists or editors to edit newsletters."""
    newsletter = get_object_or_404(
        Newsletter,
        pk=pk,
    )

    is_editor = request.user.role == User.Role.EDITOR

    is_owner = (
        request.user.role == User.Role.JOURNALIST
        and newsletter.author_id == request.user.id
    )

    if not is_editor and not is_owner:
        return HttpResponseForbidden(
            "You do not have permission to edit this newsletter."
        )

    form = NewsletterForm(
        request.POST or None,
        instance=newsletter,
        author=newsletter.author,
    )

    if form.is_valid():
        form.save()

        messages.success(
            request,
            "Newsletter updated successfully.",
        )

        return redirect(
            "newsletter-detail",
            pk=newsletter.pk,
        )

    return render(
        request,
        "news/newsletter_form.html",
        {
            "form": form,
            "newsletter": newsletter,
            "heading": "Update Newsletter",
        },
    )


@login_required
def newsletter_delete(request, pk):
    """Allow owning journalists or editors to delete newsletters."""
    newsletter = get_object_or_404(
        Newsletter,
        pk=pk,
    )

    is_editor = request.user.role == User.Role.EDITOR

    is_owner = (
        request.user.role == User.Role.JOURNALIST
        and newsletter.author_id == request.user.id
    )

    if not is_editor and not is_owner:
        return HttpResponseForbidden(
            "You do not have permission to delete this newsletter."
        )

    if request.method == "POST":
        newsletter.delete()

        messages.success(
            request,
            "Newsletter deleted successfully.",
        )

        return redirect("newsletter-list")

    return render(
        request,
        "news/newsletter_confirm_delete.html",
        {"newsletter": newsletter},
    )


@login_required
def article_create(request):
    """Allow journalists to submit articles."""
    if request.user.role != User.Role.JOURNALIST:
        return HttpResponseForbidden(
            "Only journalists may create articles."
        )

    form = ArticleForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        article = form.save(commit=False)
        article.author = request.user
        article.approved = False

        try:
            article.full_clean()
        except ValidationError as error:
            form.add_error(None, error)
        else:
            article.save()

            messages.success(
                request,
                "Article submitted for editor approval.",
            )

            return redirect("my-articles")

    return render(
        request,
        "news/article_form.html",
        {
            "form": form,
            "heading": "Create Article",
        },
    )


@login_required
def approval_queue(request):
    """Display articles awaiting editor approval."""
    if request.user.role != User.Role.EDITOR:
        return HttpResponseForbidden(
            "Only editors may access the approval queue."
        )

    articles = (
        Article.objects.filter(approved=False)
        .select_related("author", "publisher")
        .order_by("-created_at")
    )

    return render(
        request,
        "news/approval_queue.html",
        {"articles": articles},
    )


@login_required
def approve_article(request, pk):
    """Allow an editor to approve an article."""
    if request.user.role != User.Role.EDITOR:
        return HttpResponseForbidden(
            "Only editors may approve articles."
        )

    article = get_object_or_404(
        Article,
        pk=pk,
    )

    if request.method == "POST":
        article.approved = True
        article.approval_notified = False
        article.save(
            update_fields=(
                "approved",
                "approval_notified",
            )
        )

        messages.success(
            request,
            "Article approved successfully.",
        )

        return redirect("approval-queue")

    return render(
        request,
        "news/approve.html",
        {"article": article},
    )


@login_required
def subscribed_articles(request):
    """Display articles from subscribed publishers and journalists."""
    articles = (
        Article.objects
        .filter(approved=True)
        .filter(
            Q(
                publisher__in=request.user.subscribed_publishers.all()
            )
            | Q(
                author__in=request.user.subscribed_journalists.all()
            )
        )
        .distinct()
    )

    return render(
        request,
        "news/subscribed_articles.html",
        {
            "articles": articles,
        },
    )


@login_required
def article_update(request, pk):
    """Allow an owning journalist or editor to edit an article."""
    article = get_object_or_404(
        Article,
        pk=pk,
    )

    is_editor = request.user.role == User.Role.EDITOR

    is_owner = (
        request.user.role == User.Role.JOURNALIST
        and article.author_id == request.user.id
    )

    if not is_editor and not is_owner:
        return HttpResponseForbidden(
            "You do not have permission to edit this article."
        )

    form = ArticleForm(
        request.POST or None,
        instance=article,
    )

    if form.is_valid():
        updated_article = form.save(commit=False)

        if is_owner:
            updated_article.approved = False
            updated_article.approval_notified = False

        updated_article.full_clean()
        updated_article.save()

        messages.success(
            request,
            "Article updated successfully.",
        )

        if is_editor:
            return redirect("approval-queue")

        return redirect("my-articles")

    return render(
        request,
        "news/article_form.html",
        {
            "form": form,
            "article": article,
            "heading": "Update Article",
        },
    )


@login_required
def article_delete(request, pk):
    """Allow an owning journalist or editor to delete an article."""
    article = get_object_or_404(
        Article,
        pk=pk,
    )

    is_editor = request.user.role == User.Role.EDITOR

    is_owner = (
        request.user.role == User.Role.JOURNALIST
        and article.author_id == request.user.id
    )

    if not is_editor and not is_owner:
        return HttpResponseForbidden(
            "You do not have permission to delete this article."
        )

    if request.method == "POST":
        article.delete()

        messages.success(
            request,
            "Article deleted successfully.",
        )

        if is_editor:
            return redirect("article-list")

        return redirect("my-articles")

    return render(
        request,
        "news/article_confirm_delete.html",
        {"article": article},
    )


def register(request):
    """Register a reader or journalist."""
    form = RegistrationForm(request.POST or None)

    if form.is_valid():
        user = form.save()
        login(request, user)

        messages.success(
            request,
            "Registration successful.",
        )

        return redirect("article-list")

    return render(
        request,
        "registration/register.html",
        {"form": form},
    )


@login_required
def my_articles(request):
    """Display articles belonging to the journalist."""
    if request.user.role != User.Role.JOURNALIST:
        return HttpResponseForbidden(
            "Only journalists have an article workspace."
        )

    articles = (
        Article.objects.filter(author=request.user)
        .select_related("publisher")
        .order_by("-created_at")
    )

    return render(
        request,
        "news/my_articles.html",
        {"articles": articles},
    )


@login_required
def publisher_list(request):
    """Display publisher management for editors."""
    if request.user.role != User.Role.EDITOR:
        return HttpResponseForbidden(
            "Only editors may manage publishers."
        )

    publishers = Publisher.objects.prefetch_related(
        "editors",
        "journalists",
    )

    return render(
        request,
        "news/publisher_list.html",
        {"publishers": publishers},
    )


@login_required
def publisher_create(request):
    """Allow editors to create publishers."""
    if request.user.role != User.Role.EDITOR:
        return HttpResponseForbidden(
            "Only editors may create publishers."
        )

    form = PublisherForm(request.POST or None)

    if form.is_valid():
        publisher = form.save()

        if not publisher.editors.filter(
            pk=request.user.pk
        ).exists():
            publisher.editors.add(request.user)

        messages.success(
            request,
            "Publisher created successfully.",
        )

        return redirect("publisher-list")

    return render(
        request,
        "news/publisher_form.html",
        {
            "form": form,
            "heading": "Create Publisher",
        },
    )


@login_required
def publisher_update(request, pk):
    """Allow editors to update publishers."""
    if request.user.role != User.Role.EDITOR:
        return HttpResponseForbidden(
            "Only editors may update publishers."
        )

    publisher = get_object_or_404(
        Publisher,
        pk=pk,
    )

    form = PublisherForm(
        request.POST or None,
        instance=publisher,
    )

    if form.is_valid():
        form.save()

        messages.success(
            request,
            "Publisher updated successfully.",
        )

        return redirect("publisher-list")

    return render(
        request,
        "news/publisher_form.html",
        {
            "form": form,
            "publisher": publisher,
            "heading": "Update Publisher",
        },
    )


@login_required
def subscription_manage(request):
    """Display publisher and journalist subscriptions."""
    if request.user.role != User.Role.READER:
        return HttpResponseForbidden(
            "Only readers may manage subscriptions."
        )

    publishers = Publisher.objects.all().order_by("name")

    journalists = User.objects.filter(
        role=User.Role.JOURNALIST,
    ).order_by("username")

    return render(
        request,
        "news/subscription_manage.html",
        {
            "publishers": publishers,
            "journalists": journalists,
        },
    )


@login_required
def toggle_publisher_subscription(request, pk):
    """Toggle a reader's publisher subscription."""
    if request.user.role != User.Role.READER:
        return HttpResponseForbidden(
            "Only readers may manage subscriptions."
        )

    if request.method != "POST":
        return HttpResponseForbidden(
            "Subscription changes require POST."
        )

    publisher = get_object_or_404(
        Publisher,
        pk=pk,
    )

    if request.user.subscribed_publishers.filter(
        pk=publisher.pk
    ).exists():
        request.user.subscribed_publishers.remove(
            publisher
        )
        message = "Publisher subscription removed."
    else:
        request.user.subscribed_publishers.add(
            publisher
        )
        message = "Publisher subscription added."

    messages.success(request, message)

    return redirect("subscription-manage")


@login_required
def toggle_journalist_subscription(request, pk):
    """Toggle a reader's journalist subscription."""
    if request.user.role != User.Role.READER:
        return HttpResponseForbidden(
            "Only readers may manage subscriptions."
        )

    if request.method != "POST":
        return HttpResponseForbidden(
            "Subscription changes require POST."
        )

    journalist = get_object_or_404(
        User,
        pk=pk,
        role=User.Role.JOURNALIST,
    )

    if request.user.subscribed_journalists.filter(
        pk=journalist.pk
    ).exists():
        request.user.subscribed_journalists.remove(
            journalist
        )
        message = "Journalist subscription removed."
    else:
        request.user.subscribed_journalists.add(
            journalist
        )
        message = "Journalist subscription added."

    messages.success(request, message)

    return redirect("subscription-manage")
