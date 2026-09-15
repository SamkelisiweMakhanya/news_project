
from typing import ClassVar

from rest_framework import serializers  # type: ignore[reportMissingImports]

from .models import Article, Newsletter, Publisher, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields: ClassVar[list[str]] = [
            "id",
            "username",
            "email",
            "role",
        ]


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields: ClassVar[list[str]] = [
            "id",
            "name",
            "description",
            "members",
        ]


class ArticleSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    publisher = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
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
        """Validate the article's journalist/publisher relationship."""

        request = self.context.get("request")
        author = request.user if request else None
        publisher = attrs.get("publisher")

        if author is None:
            raise serializers.ValidationError(
                "An authenticated author is required."
            )

        if author.role not in (
            User.Role.JOURNALIST,
            User.Role.EDITOR,
        ):
            raise serializers.ValidationError(
                "Only journalists and editors can create articles."
            )

        if publisher is None and author.role != User.Role.JOURNALIST:
            raise serializers.ValidationError(
                "Independent articles must be created by journalists."
            )

        return attrs


class NewsletterSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
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
    author = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )
    publisher = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
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
