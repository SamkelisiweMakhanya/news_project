"""
Signal handlers for the news application's user roles and permissions.

This module creates Django groups and permissions after migrations and
automatically assigns users to the appropriate group when their role
is saved.
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import Article, Newsletter, User

ROLE_GROUPS = {
    User.Role.READER: "Reader",
    User.Role.EDITOR: "Editor",
    User.Role.JOURNALIST: "Journalist",
}


def get_permission(model, codename, name):
    """Create or retrieve a model-level Django permission."""

    content_type = ContentType.objects.get_for_model(model)

    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename=codename,
        defaults={"name": name},
    )

    return permission


@receiver(post_migrate)
def create_role_groups(sender, **kwargs):
    """
    Create role-based Django groups and assign their permissions.

    The Reader, Editor, and Journalist groups receive different
    permissions for working with articles and newsletters.
    """

    permissions = {
        "Reader": [
            get_permission(Article, "view_article", "Can view article"),
            get_permission(
                Newsletter, "view_newsletter", "Can view newsletter"
            ),
        ],
        "Editor": [
            get_permission(Article, "view_article", "Can view article"),
            get_permission(Article, "change_article", "Can change article"),
            get_permission(Article, "delete_article", "Can delete article"),
            get_permission(
                Newsletter, "view_newsletter", "Can view newsletter"
            ),
            get_permission(
                Newsletter, "change_newsletter", "Can change newsletter"
            ),
            get_permission(
                Newsletter, "delete_newsletter", "Can delete newsletter"
            ),
        ],
        "Journalist": [
            get_permission(Article, "add_article", "Can add article"),
            get_permission(Article, "view_article", "Can view article"),
            get_permission(Article, "change_article", "Can change article"),
            get_permission(Article, "delete_article", "Can delete article"),
            get_permission(Newsletter, "add_newsletter", "Can add newsletter"),
            get_permission(
                Newsletter, "view_newsletter", "Can view newsletter"
            ),
            get_permission(
                Newsletter, "change_newsletter", "Can change newsletter"
            ),
            get_permission(
                Newsletter, "delete_newsletter", "Can delete newsletter"
            ),
        ],
    }

    for group_name, group_permissions in permissions.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        group.permissions.set(group_permissions)


@receiver(post_save, sender=User)
def assign_role_group(sender, instance, **kwargs):
    """
    Assign the appropriate Django group based on the user's role.

    Existing group memberships are cleared before the user's role
    group is added.
    """

    group_name = ROLE_GROUPS.get(instance.role)

    if not group_name:
        return

    group, _ = Group.objects.get_or_create(name=group_name)

    instance.groups.clear()
    instance.groups.add(group)
