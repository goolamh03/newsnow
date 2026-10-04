"""Signal handlers for the NewsNow application.

This module contains Django signal receivers responsible for
automatic group assignment, role-based permission management,
article distribution, and webhook notifications.

Signal handlers are triggered by migration and model save
events to ensure that application data, permissions, and
notifications remain synchronized.
"""

from django.contrib.auth.models import Group, Permission
from django.core.mail import send_mail
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from .models import Article, User
import requests


@receiver(post_migrate)
def create_role_groups(sender, **kwargs):
    """Create and configure NewsNow role groups.

    Initializes the Reader, Editor, and Journalist groups
    after database migrations and assigns the appropriate
    Django permissions to each role.

    :param sender:
        Application configuration that triggered the signal.
    :type sender: AppConfig

    :param kwargs:
        Additional signal arguments supplied by Django.
    :type kwargs: dict

    :return: None
    :rtype: None
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
    """Assign role-based group membership to a user.

    Updates the user's Django group assignment whenever
    the user record is saved. Non-reader users have
    subscription relationships removed automatically.

    :param sender:
        Model class that triggered the signal.
    :type sender: type

    :param instance:
        User instance being saved.
    :type instance: User

    :param created:
        Indicates whether the user was newly created.
    :type created: bool

    :param kwargs:
        Additional signal arguments supplied by Django.
    :type kwargs: dict

    :return: None
    :rtype: None
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

    Sends email notifications to subscribed readers and
    publishes approval information to the configured
    webhook endpoint.

    Processing occurs only once per article approval.

    :param sender:
        Model class that triggered the signal.
    :type sender: type

    :param instance:
        Article instance being processed.
    :type instance: Article

    :param kwargs:
        Additional signal arguments supplied by Django.
    :type kwargs: dict

    :return: None
    :rtype: None

    :raises requests.RequestException:
        Raised if the webhook request fails. The exception
        is handled internally and does not interrupt signal
        processing.
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
