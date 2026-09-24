"""
Models for the news application.

This module defines the database models used to represent users,
publishers, articles, and newsletters, including role-based access
and subscription relationships.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Publisher(models.Model):
    """Represent a news publisher and its associated members."""

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(
        "User",
        blank=True,
        related_name="publisher_memberships",
    )

    def __str__(self):
        """Return the publisher's name as its string representation."""
        return self.name


class User(AbstractUser):
    """Represent a custom user with roles and subscription relationships."""

    class Role(models.TextChoices):
        """Define the available roles that a user can have."""

        READER = "READER", "Reader"
        EDITOR = "EDITOR", "Editor"
        JOURNALIST = "JOURNALIST", "Journalist"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.READER,
    )

    subscribed_publishers = models.ManyToManyField(
        "Publisher",
        blank=True,
        related_name="subscribed_readers",
    )

    subscribed_journalists = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="subscriber_readers",
    )


    def save(self, *args, **kwargs):
        """Keep role-specific subscription fields consistent."""

        super().save(*args, **kwargs)

        if self.role == self.Role.JOURNALIST:
            self.subscribed_publishers.clear()
            self.subscribed_journalists.clear()

        elif self.role == self.Role.READER:
            # Reader subscriptions are valid for readers.
            pass

        elif self.role == self.Role.EDITOR:
            self.subscribed_publishers.clear()
            self.subscribed_journalists.clear()

    def __str__(self):
        """Return the user's username as its string representation."""
        return self.username


class Article(models.Model):
    """Represent a news article written by an authorised user."""

    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="articles",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )

    def clean(self):
        """Validate that the article's author is permitted to write it.

    Independent articles must be written by journalists, while
    publisher articles may be written by journalists or editors.
        """
        from django.core.exceptions import ValidationError

        if self.publisher is None and self.author.role != User.Role.JOURNALIST:
            raise ValidationError(
                "An independent article must be written by a journalist."
            )

        if self.publisher is not None and self.author.role not in (
            User.Role.JOURNALIST,
            User.Role.EDITOR,
        ):
            raise ValidationError(
                "A publisher article must be written by a journalist or "
                "editor."
            )

    def __str__(self):
        """Return the article title as its string representation."""
        return self.title


class Newsletter(models.Model):
    """Represent a curated collection of news articles."""

    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="newsletters",
    )
    articles = models.ManyToManyField(
        Article,
        blank=True,
        related_name="newsletters",
    )

    def __str__(self):
        """Return the newsletter title as its string representation."""
        return self.title
