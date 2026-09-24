"""
Serializers for the news application's API.

This module defines serializers for users, publishers, articles, and
newsletters. The serializers control how model data is converted
to and from JSON for API requests and responses.
"""

from typing import ClassVar

from rest_framework import serializers  # type: ignore[reportMissingImports]

from .models import Article, Newsletter, Publisher, User


class UserSerializer(serializers.ModelSerializer):
    """Serialize user information for API responses."""

    class Meta:
        """Configure the fields included in the user serializer."""

        model = User
        fields: ClassVar[list[str]] = [
            "id",
            "username",
            "email",
            "role",
        ]


class PublisherSerializer(serializers.ModelSerializer):
    """Serialize publisher information for API requests and responses."""

    class Meta:
        """Configure the fields included in the publisher serializer."""

        model = Publisher
        fields: ClassVar[list[str]] = [
            "id",
            "name",
            "description",
            "members",
        ]


class ArticleSerializer(serializers.ModelSerializer):
    """Serialize article information and validate article creation."""

    author = UserSerializer(read_only=True)
    publisher = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        """Configure the fields and read-only fields for articles."""

        model = Article
        fields: ClassVar[list[str]] = [
            "id",
            "title",
            "content",
            "author",
            "created_at",
            "approved",
            "publisher",
        ]
        read_only_fields: ClassVar[list[str]] = [
            "created_at",
            "approved",
        ]

    def validate(self, attrs):
        """Validate the author's role and publisher relationship."""
        request = self.context.get("request")
        author = request.user if request else None
        publisher = attrs.get("publisher")

        if author is None:
            raise serializers.ValidationError(
                "An authenticated author is required."
            )

        if author.role not in (User.Role.JOURNALIST, User.Role.EDITOR):
            raise serializers.ValidationError(
                "Only journalists and editors can create articles."
            )

        if publisher is None and author.role != User.Role.JOURNALIST:
            raise serializers.ValidationError(
                "Independent articles must be created by journalists."
            )

        return attrs


class NewsletterSerializer(serializers.ModelSerializer):
    """Serialize newsletter information for API requests and responses."""

    author = UserSerializer(read_only=True)

    class Meta:
        """Configure the fields and read-only fields for newsletters."""

        model = Newsletter
        fields: ClassVar[list[str]] = [
            "id",
            "title",
            "description",
            "created_at",
            "author",
            "articles",
        ]
        read_only_fields: ClassVar[list[str]] = [
            "created_at",
        ]


class ApprovedArticleSerializer(serializers.ModelSerializer):
    """Serialize articles received through the approval workflow."""

    author = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )
    publisher = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        """Configure the fields and read-only fields for approved articles."""

        model = Article
        fields: ClassVar[list[str]] = [
            "id",
            "title",
            "content",
            "author",
            "publisher",
            "approved",
            "created_at",
        ]
        read_only_fields: ClassVar[list[str]] = [
            "id",
            "approved",
            "created_at",
        ]
