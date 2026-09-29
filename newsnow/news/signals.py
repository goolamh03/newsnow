"""Signal handlers for the NewsNow application.

Provides automatic group assignment, role-based permission setup,
article distribution, and webhook notifications triggered by model
and migration events.
"""

from django.contrib.auth.models import Group, Permission
from django.core.mail import send_mail
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from .models import Article, User
import requests


@receiver(post_migrate)
def create_role_groups(sender, **kwargs):
    """Create and configure user role groups after migrations.

    Assigns the appropriate Django permissions to the Reader,
    Editor, and Journalist groups.
    """
    if sender.name != "news":
        return
    mapping = {
        "Reader": ["view_article", "view_newsletter"],
        "Editor": [
            "view_article",
            "change_article",
            "delete_article",
            "view_newsletter",
            "change_newsletter",
            "delete_newsletter",
        ],
        "Journalist": [
            "add_article",
            "view_article",
            "change_article",
            "delete_article",
            "add_newsletter",
            "view_newsletter",
            "change_newsletter",
            "delete_newsletter",
        ],
    }
    for name, codes in mapping.items():
        group, _ = Group.objects.get_or_create(name=name)
        group.permissions.set(Permission.objects.filter(codename__in=codes))


@receiver(post_save, sender=User)
def assign_group_and_token(sender, instance, created, **kwargs):
    """Assign users to role-based groups after saving.

    Updates group membership based on the user's role and
    clears subscriptions for non-reader accounts.
    """
    group_name = instance.get_role_display()

    instance.groups.clear()

    group, _ = Group.objects.get_or_create(name=group_name)

    instance.groups.add(group)

    if instance.role != User.Role.READER:
        instance.subscribed_publishers.clear()
        instance.subscribed_journalists.clear()


@receiver(post_save, sender=Article)
def distribute_approved_article(sender, instance, **kwargs):
    """Distribute approved articles and notify subscribers.

    Sends article notifications to subscribed users and
    posts approval information to the external webhook endpoint.
    """
    if not instance.approved or instance.approval_notified:
        return
    publisher_emails = (
        list(instance.publisher.subscribers.exclude
             (email="").values_list("email", flat=True))
        if instance.publisher
        else []
    )
    journalist_emails = list(
        instance.author.journalist_subscribers.exclude
        (email="").values_list("email", flat=True)
    )
    recipients = sorted(set(publisher_emails + list(journalist_emails)))
    if recipients:
        send_mail(
            f"NewsNow: {instance.title}",
            instance.content,
            None,
            recipients,
            fail_silently=False,
        )
    try:
        requests.post(
            "http://127.0.0.1:8000/api/approved/",
            json={
                "article": instance.pk,
                "payload": {
                    "article": instance.pk,
                    "title": instance.title,
                    "author": instance.author.username,
                    "publisher": (
                        instance.publisher.name
                        if instance.publisher
                        else None
                    ),
                },
            },
            timeout=5,
        )
    except requests.RequestException:
        pass
    finally:
        Article.objects.filter(pk=instance.pk).update(approval_notified=True)
