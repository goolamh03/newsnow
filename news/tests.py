"""Automated tests for the NewsNow application.

This module contains unit and integration tests covering
REST API endpoints, role-based permissions, web views,
signal processing, email notifications, newsletter
management, and approved article webhook integrations.

The tests verify application behaviour for readers,
journalists, editors, and anonymous users.
"""

from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Article, Publisher, User, Newsletter


class APITests(APITestCase):
    """Test REST API functionality.

    Covers article management, article approval,
    permissions, newsletter functionality, and
    subscription-based article retrieval."""

    def setUp(self):
        """Create test data for API tests.

        Initializes reader, journalist, and editor accounts,
        a test publisher, and an approved article used
        throughout the API test suite.

        :return: None
        :rtype: None"""
        self.reader = User.objects.create_user(
            "reader",
            email="r@example.com",
            password="pass12345",
            role=User.Role.READER,
        )

        self.journalist = User.objects.create_user(
            "journo",
            password="pass12345",
            role=User.Role.JOURNALIST,
        )

        self.editor = User.objects.create_user(
            "editor",
            password="pass12345",
            role=User.Role.EDITOR,
        )

        self.publisher = Publisher.objects.create(
            name="Daily Test"
        )

        self.publisher.journalists.add(
            self.journalist
        )

        self.article = Article.objects.create(
            title="Approved",
            content="Body",
            author=self.journalist,
            publisher=self.publisher,
            approved=True,
        )

    def auth(self, user):
        """Authenticate a user for API requests.

        :param user: User that should be authenticated.
        :type user: User

        :return: None
        :rtype: None"""
        self.client.force_authenticate(user)

    def test_reader_only_gets_subscribed_articles(self):
        """Verify readers receive articles from subscribed publishers."""
        self.reader.subscribed_publishers.add(
            self.publisher
        )

        self.auth(self.reader)

        response = self.client.get(
            "/api/articles/subscribed/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

    def test_reader_cannot_create_article(self):
        """Verify readers cannot create articles."""
        self.auth(self.reader)

        response = self.client.post(
            "/api/articles/",
            {
                "title": "No",
                "content": "No",
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_journalist_can_create_article(self):
        """Verify a journalist can create an article.

        Confirms that newly created articles are assigned
        to the authenticated journalist and remain
        unapproved pending editorial review.

        :return: None
        :rtype: None"""
        self.auth(self.journalist)

        response = self.client.post(
            "/api/articles/",
            {
                "title": "Draft",
                "content": "Draft article content.",
                "publisher": self.publisher.pk,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
            response.data,
        )

        article = Article.objects.get(
            title="Draft"
        )

        self.assertEqual(
            article.author,
            self.journalist,
        )

        self.assertFalse(
            article.approved
        )

    def test_editor_can_delete(self):
        """Verify editors can delete articles."""
        self.auth(self.editor)

        response = self.client.delete(
            f"/api/articles/{self.article.pk}/"
        )

        self.assertEqual(
            response.status_code,
            204,
        )

    def test_editor_can_approve_article(self):
        """Verify editors can approve articles."""
        self.article.approved = False
        self.article.save()

        self.auth(self.editor)

        response = self.client.post(
            f"/api/articles/{self.article.pk}/approve/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.article.refresh_from_db()

        self.assertTrue(
            self.article.approved
        )

    def test_reader_cannot_approve_article(self):
        """Verify readers cannot approve articles."""
        self.auth(self.reader)

        response = self.client.post(
            f"/api/articles/{self.article.pk}/approve/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_get_single_article(self):
        """Verify a reader can retrieve a single article."""
        self.auth(self.reader)

        response = self.client.get(
            f"/api/articles/{self.article.pk}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["title"],
            self.article.title,
        )

    def test_journalist_can_update_article(self):
        """Verify journalists can update their own articles."""
        self.auth(self.journalist)

        response = self.client.put(
            f"/api/articles/{self.article.pk}/",
            {
                "title": "Updated Title",
                "content": "Updated Body",
                "publisher": self.publisher.pk,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.article.refresh_from_db()

        self.assertEqual(
            self.article.title,
            "Updated Title",
        )

    def test_unauthenticated_user_denied(self):
        """Verify anonymous users cannot access protected endpoints."""
        response = self.client.get(
            "/api/articles/"
        )

        self.assertIn(
            response.status_code,
            [401, 403],
        )

    def test_newsletter_creation(self):
        """Verify journalists can create newsletters."""
        newsletter = Newsletter.objects.create(
            title="Weekly News",
            description="Weekly summary",
            author=self.journalist,
        )

        newsletter.articles.add(
            self.article
        )

        self.assertEqual(
            newsletter.title,
            "Weekly News",
        )

        self.assertEqual(
            newsletter.articles.count(),
            1,
        )

    def test_journalist_cannot_delete_other_article(self):
        """Verify journalists cannot delete another journalist's article."""
        other = User.objects.create_user(
            "other",
            password="pass12345",
            role=User.Role.JOURNALIST,
        )

        self.auth(other)

        response = self.client.delete(
            f"/api/articles/{self.article.pk}/"
        )

        self.assertIn(
            response.status_code,
            [403, 404],
        )


class ViewTests(TestCase):
    """Test web views and role-based access control.

    Verifies page rendering, permissions,
    subscriptions, article management,
    newsletter management, and registration
    workflows."""

    def setUp(self):
        """Create test data for view tests.

        Creates users, publishers, approved articles,
        pending articles, and newsletters used by the
        web application test suite.

        :return: None
        :rtype: None"""
        self.reader = User.objects.create_user(
            username="view_reader",
            email="view_reader@example.com",
            password="pass12345",
            role=User.Role.READER,
        )

        self.journalist = User.objects.create_user(
            username="view_journalist",
            email="view_journalist@example.com",
            password="pass12345",
            role=User.Role.JOURNALIST,
        )

        self.other_journalist = User.objects.create_user(
            username="other_journalist",
            email="other@example.com",
            password="pass12345",
            role=User.Role.JOURNALIST,
        )

        self.editor = User.objects.create_user(
            username="view_editor",
            email="view_editor@example.com",
            password="pass12345",
            role=User.Role.EDITOR,
        )

        self.publisher = Publisher.objects.create(
            name="View Test Publisher",
            description="Publisher used by view tests.",
        )

        self.publisher.journalists.add(
            self.journalist,
            self.other_journalist,
        )

        self.approved_article = Article.objects.create(
            title="Approved View Article",
            content="Approved article content.",
            author=self.journalist,
            publisher=self.publisher,
            approved=True,
        )

        self.pending_article = Article.objects.create(
            title="Pending View Article",
            content="Pending article content.",
            author=self.journalist,
            publisher=self.publisher,
            approved=False,
        )

        self.newsletter = Newsletter.objects.create(
            title="View Test Newsletter",
            description="Newsletter used by view tests.",
            author=self.journalist,
        )

        self.newsletter.articles.add(self.approved_article)

    def test_article_list_displays_only_approved_articles(self):
        """Verify the article detail page renders correctly.

        Ensures the page loads successfully and displays
        the expected article title and content.

        :return: None
        :rtype: None"""
        response = self.client.get(
            reverse("article-list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "news/article_list.html",
        )
        self.assertContains(
            response,
            self.approved_article.title,
        )
        self.assertNotContains(
            response,
            self.pending_article.title,
        )

    def test_article_detail_displays_approved_article(self):
        """Verify an approved article's detail page is displayed."""
        response = self.client.get(
            reverse(
                "article-detail",
                args=[self.approved_article.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "news/article_detail.html",
        )
        self.assertEqual(
            response.context["article"],
            self.approved_article,
        )

    def test_article_detail_returns_404_for_pending_article(self):
        """Verify pending articles are unavailable on the detail page."""
        response = self.client.get(
            reverse(
                "article-detail",
                args=[self.pending_article.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_article_detail_returns_404_for_unknown_article(self):
        """Verify an unknown article ID returns a not-found response."""
        response = self.client.get(
            reverse(
                "article-detail",
                args=[99999],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_newsletter_list_displays_newsletters(self):
        """Verify the newsletter list displays available newsletters."""
        response = self.client.get(
            reverse("newsletter-list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "news/newsletter_list.html",
        )
        self.assertContains(
            response,
            self.newsletter.title,
        )

    def test_reader_can_view_newsletter_detail(self):
        """Verify readers can open a newsletter."""

        self.client.force_login(self.reader)

        response = self.client.get(
            reverse(
                "newsletter-detail",
                args=[self.newsletter.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "news/newsletter_detail.html",
        )

        self.assertContains(
            response,
            self.newsletter.title,
        )

    def test_reader_can_access_subscription_management(self):
        """Verify readers can manage subscriptions."""

        self.client.force_login(self.reader)

        response = self.client.get(
            reverse("subscription-manage")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Publishers",
        )

        self.assertContains(
            response,
            "Journalists",
        )

    def test_reader_can_unsubscribe_from_journalist(self):
        """Verify readers can unsubscribe from journalists."""

        self.reader.subscribed_journalists.add(
            self.journalist
        )

        self.client.force_login(
            self.reader
        )

        response = self.client.post(
            reverse(
                "toggle-journalist-subscription",
                args=[self.journalist.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("subscription-manage"),
        )

        self.reader.refresh_from_db()

        self.assertFalse(
            self.reader.subscribed_journalists.filter(
                pk=self.journalist.pk
            ).exists()
        )

    def test_reader_feed_shows_subscribed_journalist_articles(self):
        """Verify subscribed journalist articles appear in the feed."""

        self.reader.subscribed_journalists.add(
            self.journalist
        )

        self.client.force_login(
            self.reader
        )

        response = self.client.get(
            reverse("subscribed-articles")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            self.approved_article.title,
        )

    def test_journalist_cannot_access_subscription_management(self):
        """Verify journalists cannot access reader subscriptions."""

        self.client.force_login(
            self.journalist
        )

        response = self.client.get(
            reverse("subscription-manage")
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_reader_can_subscribe_to_journalist(self):
        """Verify readers can subscribe to journalists."""

        self.client.force_login(
            self.reader
        )

        response = self.client.post(
            reverse(
                "toggle-journalist-subscription",
                args=[self.journalist.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("subscription-manage"),
        )

        self.reader.refresh_from_db()

        self.assertTrue(
            self.reader.subscribed_journalists.filter(
                pk=self.journalist.pk
            ).exists()
        )

    def test_anonymous_user_cannot_access_article_create(self):
        """Verify anonymous users are redirected from article creation."""
        response = self.client.get(
            reverse("article-create")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("login"),
            response.url,
        )

    def test_reader_cannot_access_article_create(self):
        """Verify readers cannot access the article creation view."""
        self.client.force_login(self.reader)

        response = self.client.get(
            reverse("article-create")
        )

        self.assertEqual(response.status_code, 403)

    def test_editor_cannot_access_article_create(self):
        """Verify editors cannot access the article creation view."""
        self.client.force_login(self.editor)

        response = self.client.get(
            reverse("article-create")
        )

        self.assertEqual(response.status_code, 403)

    def test_journalist_can_open_article_create_form(self):
        """Verify journalists can open the article creation form."""
        self.client.force_login(self.journalist)

        response = self.client.get(
            reverse("article-create")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "news/article_form.html",
        )
        self.assertIn("form", response.context)

    def test_journalist_can_create_article(self):
        """Verify journalists can create unapproved articles."""
        self.publisher.journalists.add(
            self.journalist
        )

        self.client.force_login(
            self.journalist
        )

        response = self.client.post(
            reverse("article-create"),
            {
                "title": "Journalist Web Article",
                "content": "Article submitted through the web form.",
                "publisher": self.publisher.pk,
            },
        )

        if response.status_code == 200:
            self.fail(
                f"Article form errors: "
                f"{response.context['form'].errors.as_json()}"
            )

        self.assertEqual(
            response.status_code,
            302,
        )

        article = Article.objects.get(
            title="Journalist Web Article"
        )

        self.assertEqual(
            article.author,
            self.journalist,
        )

        self.assertFalse(
            article.approved
        )

    def test_invalid_article_create_form_is_redisplayed(self):
        """Verify invalid article data redisplays the creation form."""
        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse("article-create"),
            {
                "title": "",
                "content": "",
                "publisher": self.publisher.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "news/article_form.html",
        )
        self.assertTrue(
            response.context["form"].errors
        )

    def test_anonymous_user_cannot_access_approval_queue(self):
        """Verify anonymous users are redirected from approvals."""
        response = self.client.get(
            reverse("approval-queue")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("login"),
            response.url,
        )

    def test_reader_cannot_access_approval_queue(self):
        """Verify readers cannot access the approval queue."""
        self.client.force_login(self.reader)

        response = self.client.get(
            reverse("approval-queue")
        )

        self.assertEqual(response.status_code, 403)

    def test_journalist_cannot_access_approval_queue(self):
        """Verify journalists cannot access the approval queue."""
        self.client.force_login(self.journalist)

        response = self.client.get(
            reverse("approval-queue")
        )

        self.assertEqual(response.status_code, 403)

    def test_editor_can_view_pending_articles(self):
        """Verify editors can view pending articles in the queue."""
        self.client.force_login(self.editor)

        response = self.client.get(
            reverse("approval-queue")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "news/approval_queue.html",
        )
        self.assertContains(
            response,
            self.pending_article.title,
        )
        self.assertNotContains(
            response,
            self.approved_article.title,
        )

    def test_reader_cannot_approve_article(self):
        """Verify readers cannot approve pending articles."""
        self.client.force_login(self.reader)

        response = self.client.post(
            reverse(
                "article-approve",
                args=[self.pending_article.pk],
            )
        )

        self.assertEqual(response.status_code, 403)

        self.pending_article.refresh_from_db()
        self.assertFalse(self.pending_article.approved)

    def test_newsletter_detail_is_displayed(self):
        """Verify newsletter detail page renders correctly."""
        self.client.force_login(self.reader)

        response = self.client.get(
            reverse(
                "newsletter-detail",
                args=[self.newsletter.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "news/newsletter_detail.html",
        )

        self.assertContains(
            response,
            self.newsletter.title,
        )

        self.assertContains(
            response,
            self.newsletter.description,
        )

    def test_newsletter_detail_contains_action_buttons(self):
        """Verify newsletter action buttons render."""

        self.client.force_login(
            self.journalist
        )

        response = self.client.get(
            reverse(
                "newsletter-detail",
                args=[self.newsletter.pk],
            )
        )

        self.assertContains(
            response,
            "Edit Newsletter",
        )

        self.assertContains(
            response,
            "Delete Newsletter",
        )

    def test_article_detail_renders_correctly(self):
        """Verify article detail page renders correctly."""

        response = self.client.get(
            reverse(
                "article-detail",
                args=[self.approved_article.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "news/article_detail.html",
        )

        self.assertContains(
            response,
            self.approved_article.title,
        )

        self.assertContains(
            response,
            self.approved_article.content,
        )

    def test_editor_can_view_publisher_list(self):
        """Verify editor can view publisher list page."""

        self.client.force_login(
            self.editor
        )

        response = self.client.get(
            reverse("publisher-list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "news/publisher_list.html",
        )

        self.assertContains(
            response,
            self.publisher.name,
        )

    def test_editor_can_open_publisher_create_form(self):
        """Verify editor can open publisher creation form."""

        self.client.force_login(
            self.editor
        )

        response = self.client.get(
            reverse("publisher-create")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "news/publisher_form.html",
        )

        self.assertContains(
            response,
            "Create Publisher",
        )

    def test_journalist_can_view_my_articles(self):
        """Verify journalist can view personal article dashboard."""

        self.client.force_login(
            self.journalist
        )

        response = self.client.get(
            reverse("my-articles")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "news/my_articles.html",
        )

        self.assertContains(
            response,
            self.approved_article.title,
        )

        self.assertContains(
            response,
            self.pending_article.title,
        )

    def test_reader_can_view_subscription_management(self):
        """Verify reader can access subscription management."""

        self.client.force_login(
            self.reader
        )

        response = self.client.get(
            reverse("subscription-manage")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "news/subscription_manage.html",
        )

        self.assertContains(
            response,
            "Publishers",
        )

        self.assertContains(
            response,
            "Journalists",
        )

    def test_newsletter_detail_renders_correctly(self):
        """Verify newsletter detail page renders correctly."""

        self.client.force_login(
            self.reader
        )

        response = self.client.get(
            reverse(
                "newsletter-detail",
                args=[self.newsletter.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "news/newsletter_detail.html",
        )

        self.assertContains(
            response,
            self.newsletter.title,
        )

    def test_newsletter_detail_contains_buttons(self):
        """Verify newsletter edit and delete buttons render."""

        self.client.force_login(
            self.journalist
        )

        response = self.client.get(
            reverse(
                "newsletter-detail",
                args=[self.newsletter.pk],
            )
        )

        self.assertContains(
            response,
            "Edit Newsletter",
        )

        self.assertContains(
            response,
            "Delete Newsletter",
        )

        self.assertContains(
            response,
            reverse(
                "newsletter-update",
                args=[self.newsletter.pk],
            ),
        )

        self.assertContains(
            response,
            reverse(
                "newsletter-delete",
                args=[self.newsletter.pk],
            ),
        )

    def test_duplicate_email_registration_rejected(self):
        """Verify duplicate email addresses are rejected."""

        User.objects.create_user(
            username="user1",
            email="duplicate@example.com",
            password="pass12345",
            role=User.Role.READER,
        )

        response = self.client.post(
            reverse("register"),
            {
                "username": "user2",
                "email": "duplicate@example.com",
                "role": User.Role.READER,
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "already exists",
        )

    @patch("news.signals.requests.post")
    def test_editor_can_approve_article(self, mock_post):
        """Verify editors can approve pending articles."""
        mock_post.return_value.status_code = 201
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                "article-approve",
                args=[self.pending_article.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("approval-queue"),
        )

        self.pending_article.refresh_from_db()
        self.assertTrue(self.pending_article.approved)
        self.assertTrue(
            self.pending_article.approval_notified
        )
        mock_post.assert_called_once()

    def test_approve_article_returns_404_for_unknown_article(self):
        """Verify approval of an unknown article returns 404."""
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                "article-approve",
                args=[99999],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_subscribed_articles_requires_authentication(self):
        """Verify subscriptions require an authenticated user."""
        response = self.client.get(
            reverse("subscribed-articles")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("login"),
            response.url,
        )

    def test_reader_sees_publisher_subscription_articles(self):
        """Verify readers see articles from subscribed publishers."""
        self.reader.subscribed_publishers.add(
            self.publisher
        )
        self.client.force_login(self.reader)

        response = self.client.get(
            reverse("subscribed-articles")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "news/subscribed_articles.html",
        )
        self.assertContains(
            response,
            self.approved_article.title,
        )
        self.assertNotContains(
            response,
            self.pending_article.title,
        )

    def test_reader_sees_journalist_subscription_articles(self):
        """Verify readers see articles from subscribed journalists."""
        self.reader.subscribed_journalists.add(
            self.journalist
        )
        self.client.force_login(self.reader)

        response = self.client.get(
            reverse("subscribed-articles")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.approved_article.title,
        )

    def test_subscribed_articles_do_not_contain_duplicates(self):
        """Verify matching subscriptions do not duplicate articles."""
        self.reader.subscribed_publishers.add(
            self.publisher
        )
        self.reader.subscribed_journalists.add(
            self.journalist
        )
        self.client.force_login(self.reader)

        response = self.client.get(
            reverse("subscribed-articles")
        )

        articles = list(
            response.context["articles"]
        )

        self.assertEqual(
            articles.count(self.approved_article),
            1,
        )

    def test_article_update_requires_authentication(self):
        """Verify updating an article requires authentication."""
        response = self.client.get(
            reverse(
                "article-update",
                args=[self.approved_article.pk],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("login"),
            response.url,
        )

    def test_article_author_can_open_update_form(self):
        """Verify the article author can open the update form."""
        self.client.force_login(self.journalist)

        response = self.client.get(
            reverse(
                "article-update",
                args=[self.approved_article.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "news/article_form.html",
        )
        self.assertEqual(
            response.context["article"],
            self.approved_article,
        )

    def test_article_author_can_update_article(self):
        """Verify the article author can update the article."""
        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse(
                "article-update",
                args=[self.approved_article.pk],
            ),
            {
                "title": "Updated View Article",
                "content": "Updated view content.",
                "publisher": self.publisher.pk,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.approved_article.refresh_from_db()

        self.assertEqual(
            self.approved_article.title,
            "Updated View Article",
        )
        self.assertEqual(
            self.approved_article.content,
            "Updated view content.",
        )

    def test_editor_can_update_article(self):
        """Verify editors can update another user's article."""
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                "article-update",
                args=[self.approved_article.pk],
            ),
            {
                "title": "Editor Updated Article",
                "content": "Content updated by editor.",
                "publisher": self.publisher.pk,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.approved_article.refresh_from_db()
        self.assertEqual(
            self.approved_article.title,
            "Editor Updated Article",
        )

    def test_other_journalist_cannot_update_article(self):
        """Verify another journalist cannot update the article."""
        self.client.force_login(
            self.other_journalist
        )

        response = self.client.get(
            reverse(
                "article-update",
                args=[self.approved_article.pk],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_invalid_article_update_form_is_redisplayed(self):
        """Verify invalid updates redisplay the article form."""
        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse(
                "article-update",
                args=[self.approved_article.pk],
            ),
            {
                "title": "",
                "content": "",
                "publisher": self.publisher.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "news/article_form.html",
        )
        self.assertTrue(
            response.context["form"].errors
        )

    def test_article_delete_requires_authentication(self):
        """Verify deleting an article requires authentication."""
        response = self.client.get(
            reverse(
                "article-delete",
                args=[self.approved_article.pk],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("login"),
            response.url,
        )

    def test_article_author_can_open_delete_page(self):
        """Verify the article author can open the delete page."""
        self.client.force_login(self.journalist)

        response = self.client.get(
            reverse(
                "article-delete",
                args=[self.approved_article.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "news/article_confirm_delete.html",
        )
        self.assertEqual(
            response.context["article"],
            self.approved_article,
        )

    def test_other_journalist_cannot_delete_article(self):
        """Verify another journalist cannot delete the article."""
        self.client.force_login(
            self.other_journalist
        )

        response = self.client.post(
            reverse(
                "article-delete",
                args=[self.approved_article.pk],
            )
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            Article.objects.filter(
                pk=self.approved_article.pk
            ).exists()
        )

    def test_article_author_can_delete_article(self):
        """Verify the article author can delete the article."""
        article_pk = self.approved_article.pk
        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse(
                "article-delete",
                args=[article_pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("my-articles"),
        )
        self.assertFalse(
            Article.objects.filter(
                pk=article_pk
            ).exists()
        )

    def test_editor_can_delete_article(self):
        """Verify editors can delete another user's article."""
        article_pk = self.approved_article.pk
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                "article-delete",
                args=[article_pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("article-list"),
        )
        self.assertFalse(
            Article.objects.filter(
                pk=article_pk
            ).exists()
        )

    def test_registration_page_is_displayed(self):
        """Verify the registration page is displayed."""
        response = self.client.get(
            reverse("register")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "registration/register.html",
        )
        self.assertIn("form", response.context)

    def test_user_can_register(self):
        """Verify a visitor can register a NewsNow account."""
        response = self.client.post(
            reverse("register"),
            {
                "username": "registered_reader",
                "email": "registered@example.com",
                "role": User.Role.READER,
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("article-list"),
        )
        self.assertTrue(
            User.objects.filter(
                username="registered_reader"
            ).exists()
        )

        registered_user = User.objects.get(
            username="registered_reader"
        )

        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            registered_user.pk,
        )

        success_messages = [
            str(message)
            for message in response.wsgi_request._messages
        ]

        self.assertIn(
            "Registration successful.",
            success_messages,
        )

    def test_editor_can_register(self):
        """Verify an editor account can be created."""

        response = self.client.post(
            reverse("register"),
            {
                "username": "new_editor",
                "email": "editor@example.com",
                "role": User.Role.EDITOR,
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("article-list"),
        )

        self.assertTrue(
            User.objects.filter(
                username="new_editor",
                role=User.Role.EDITOR,
            ).exists()
        )

    def test_invalid_registration_is_redisplayed(self):
        """Verify invalid registration data redisplays the form."""
        response = self.client.post(
            reverse("register"),
            {
                "username": "invalid_reader",
                "email": "invalid@example.com",
                "role": User.Role.READER,
                "password1": "StrongPass123!",
                "password2": "DifferentPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "registration/register.html",
        )
        self.assertTrue(
            response.context["form"].errors
        )
        self.assertFalse(
            User.objects.filter(
                username="invalid_reader"
            ).exists()
        )


class WebRoleTests(TestCase):
    """Test role-specific web functionality.

    Validates the actions available to readers,
    journalists, and editors across the web
    application."""

    def setUp(self):
        """Create role-based test records.

        Generates users, publishers, articles,
        and newsletters required for role
        validation tests.

        :return: None
        :rtype: None"""
        self.reader = User.objects.create_user(
            "reader-web",
            password="pass12345",
            role=User.Role.READER,
        )

        self.journalist = User.objects.create_user(
            "journalist-web",
            password="pass12345",
            role=User.Role.JOURNALIST,
        )

        self.editor = User.objects.create_user(
            "editor-web",
            password="pass12345",
            role=User.Role.EDITOR,
        )

        self.publisher = Publisher.objects.create(
            name="Web Publisher"
        )

        self.publisher.journalists.add(
            self.journalist
        )

        self.article = Article.objects.create(
            title="Web Article",
            content="Body",
            author=self.journalist,
            publisher=self.publisher,
        )

        self.newsletter = Newsletter.objects.create(
            title="Web Newsletter",
            description="Summary",
            author=self.journalist,
        )

    def test_journalist_can_edit_own_article(self):
        """Journalist can access own article update page."""
        self.client.force_login(self.journalist)

        response = self.client.get(
            reverse(
                "article-update",
                args=[self.article.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_journalist_can_delete_own_article(self):
        """Journalist can delete own article."""
        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse(
                "article-delete",
                args=[self.article.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("my-articles"),
        )

        self.assertFalse(
            Article.objects.filter(
                pk=self.article.pk
            ).exists()
        )

    def test_editor_can_edit_article(self):
        """Editor can access article update page."""
        self.client.force_login(self.editor)

        response = self.client.get(
            reverse(
                "article-update",
                args=[self.article.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_journalist_can_create_newsletter(self):
        """Journalist can access newsletter creation."""
        self.client.force_login(self.journalist)

        response = self.client.get(
            reverse("newsletter-create")
        )

        self.assertEqual(response.status_code, 200)

    def test_editor_can_edit_newsletter(self):
        """Editor can access newsletter update."""
        self.client.force_login(self.editor)

        response = self.client.get(
            reverse(
                "newsletter-update",
                args=[self.newsletter.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_editor_can_create_publisher(self):
        """Editor can access publisher creation."""
        self.client.force_login(self.editor)

        response = self.client.get(
            reverse("publisher-create")
        )

        self.assertEqual(response.status_code, 200)

    def test_reader_can_view_newsletters(self):
        """Reader can view the newsletter list."""
        self.client.force_login(self.reader)

        response = self.client.get(
            reverse("newsletter-list")
        )

        self.assertEqual(response.status_code, 200)

    def test_reader_can_subscribe_to_journalist(self):
        """Reader can subscribe to a journalist."""
        self.client.force_login(self.reader)

        self.client.post(
            reverse(
                "toggle-journalist-subscription",
                args=[self.journalist.pk],
            )
        )

        self.assertTrue(
            self.reader.subscribed_journalists.filter(
                pk=self.journalist.pk
            ).exists()
        )


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
)
class SignalTests(TestCase):
    """Test signal-driven functionality.

    Verifies article notification processing,
    email distribution, webhook integrations,
    and approval tracking behaviour."""

    def setUp(self):
        """Create test records for signal tests.

        Creates users and article data required
        to verify approval notifications and
        webhook processing.

        :return: None
        :rtype: None"""
        self.journalist = User.objects.create_user(
            "j",
            password="pass12345",
            role=User.Role.JOURNALIST,
        )

        self.editor = User.objects.create_user(
            "editor",
            password="pass12345",
            role=User.Role.EDITOR,
        )

        self.reader = User.objects.create_user(
            "r",
            email="reader@example.com",
            password="pass12345",
            role=User.Role.READER,
        )

        self.article = Article.objects.create(
            title="Signal",
            content="Body",
            author=self.journalist,
        )

    def auth(self, user):
        """Authenticate a user for test requests.

        :param user: User to authenticate.
        :type user: User

        :return: None
        :rtype: None"""
        self.client.force_authenticate(user)

    @patch("news.signals.requests.post")
    def test_approval_emails_subscriber_and_logs_once(
        self,
        mock_post,
    ):
        """Verify article approval triggers notifications.

        Confirms that approval sends a single email,
        calls the webhook endpoint once, and marks
        the article as notified.

        :param mock_post:
            Mocked HTTP POST request object.
        :type mock_post: Mock

        :return: None
        :rtype: None"""
        mock_post.return_value.status_code = 201

        self.reader.subscribed_journalists.add(
            self.journalist
        )

        self.article.approved = True
        self.article.save()

        self.article.refresh_from_db()

        self.assertTrue(
            self.article.approval_notified
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        mock_post.assert_called_once()

    @patch("news.signals.requests.post")
    def test_approved_endpoint_called_with_article_data(
        self,
        mock_post,
    ):
        """
        Verify article approval data is sent to the
        approved article webhook endpoint.
        """

        mock_post.return_value.status_code = 201

        self.article.approved = True
        self.article.save()

        mock_post.assert_called_once()

        args, kwargs = mock_post.call_args

        self.assertEqual(
            args[0],
            "http://127.0.0.1:8000/api/approved/",
        )

        self.assertEqual(
            kwargs["json"]["article"],
            self.article.pk,
        )

        self.assertEqual(
            kwargs["json"]["payload"]["title"],
            self.article.title,
        )

        self.assertEqual(
            kwargs["json"]["payload"]["author"],
            self.journalist.username,
        )
