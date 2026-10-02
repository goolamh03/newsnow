"""URL configuration for the NewsNow application.

Defines web and API routes for article management, newsletters,
user authentication, subscriptions, article approvals, and
webhook integrations.
"""

from django.contrib.auth import views as auth_views
from django.urls import path
from . import api_views, views
from .api_views import ArticleApprovalAPIView
from news.forms import BootstrapAuthenticationForm

urlpatterns = [
    path("", views.article_list, name="article-list"),
    path("articles/new/", views.article_create, name="article-create"),
    path("articles/<int:pk>/", views.article_detail, name="article-detail"),
    path("editor/approvals/", views.approval_queue, name="approval-queue"),
    path(
        "editor/approvals/<int:pk>/",
        views.approve_article,
        name="article-approve",
    ),
    path(
        "api/articles/",
        api_views.ArticleListCreateAPI.as_view(),
        name="api-articles",
    ),
    path(
        "api/articles/subscribed/",
        api_views.SubscribedArticlesAPI.as_view(),
        name="api-subscribed",
    ),
    path(
        "api/articles/<int:pk>/",
        api_views.ArticleDetailAPI.as_view(),
        name="api-article-detail",
    ),
    path(
        "api/approved/",
        api_views.ApprovedArticleWebhookAPI.as_view(),
        name="api-approved",
    ),
    path(
        "api/articles/<int:pk>/approve/",
        ArticleApprovalAPIView.as_view(),
        name="api-article-approve",
    ),
    path(
        "subscriptions/",
        views.subscribed_articles,
        name="subscribed-articles",
    ),
    path(
        "articles/<int:pk>/edit/",
        views.article_update,
        name="article-update",
    ),
    path(
        "articles/<int:pk>/delete/",
        views.article_delete,
        name="article-delete",
    ),
    path(
        "register/",
        views.register,
        name="register",
    ),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=BootstrapAuthenticationForm,
        ),
        name="login",
    ),
    path(
        "articles/mine/",
        views.my_articles,
        name="my-articles",
    ),

    # Newsletters
    path(
        "newsletters/",
        views.newsletter_list,
        name="newsletter-list"
    ),
    path(
        "newsletters/new/",
        views.newsletter_create,
        name="newsletter-create",
    ),
    path(
        "newsletters/<int:pk>/",
        views.newsletter_detail,
        name="newsletter-detail",
    ),
    path(
        "newsletters/<int:pk>/edit/",
        views.newsletter_update,
        name="newsletter-update",
    ),
    path(
        "newsletters/<int:pk>/delete/",
        views.newsletter_delete,
        name="newsletter-delete",
    ),

    # Publishers
    path(
        "publishers/",
        views.publisher_list,
        name="publisher-list",
    ),
    path(
        "publishers/new/",
        views.publisher_create,
        name="publisher-create",
    ),
    path(
        "publishers/<int:pk>/edit/",
        views.publisher_update,
        name="publisher-update",
    ),

    # Reader subscriptions
    path(
        "subscriptions/manage/",
        views.subscription_manage,
        name="subscription-manage",
    ),
    path(
        "subscriptions/publishers/<int:pk>/toggle/",
        views.toggle_publisher_subscription,
        name="toggle-publisher-subscription",
    ),
    path(
        "subscriptions/journalists/<int:pk>/toggle/",
        views.toggle_journalist_subscription,
        name="toggle-journalist-subscription",
    ),
    path(
        "subscriptions/",
        views.subscribed_articles,
        name="subscribed-articles",
    ),
]
