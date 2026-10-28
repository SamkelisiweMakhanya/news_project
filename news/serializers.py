"""Serializers for the REST API."""

from rest_framework import serializers

from .models import Article, Newsletter, Publisher, User


class UserSerializer(serializers.ModelSerializer):
    """Serialize a user without exposing password data."""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
        )
        read_only_fields = ("id", "role")


class PublisherSerializer(serializers.ModelSerializer):
    """Serialize publishers and their linked staff."""

    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(
            role__in=(User.Role.EDITOR, User.Role.JOURNALIST)
        ),
        required=False,
    )

    class Meta:
        model = Publisher
        fields = ("id", "name", "description", "members")


class ArticleSerializer(serializers.ModelSerializer):
    """Serialize articles and enforce author/publisher rules."""

    author = UserSerializer(read_only=True)
    publisher = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Article
        fields = (
            "id",
            "title",
            "content",
            "author",
            "created_at",
            "approved",
            "publisher",
        )
        read_only_fields = ("id", "author", "created_at", "approved")

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")
        publisher = attrs.get("publisher")
        if (
            user.role == User.Role.JOURNALIST
            and publisher
            and not publisher.members.filter(pk=user.pk).exists()
        ):
            raise serializers.ValidationError(
                "You are not linked to this publisher."
            )
        return attrs


class NewsletterSerializer(serializers.ModelSerializer):
    """Serialize newsletters without exposing unapproved articles."""

    author = UserSerializer(read_only=True)
    articles = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Article.objects.filter(approved=True),
        required=False,
    )

    class Meta:
        model = Newsletter
        fields = (
            "id",
            "title",
            "description",
            "author",
            "articles",
            "created_at",
        )
        read_only_fields = ("id", "created_at", "author")

    def to_representation(self, instance):
        """Return approved article IDs only."""
        data = super().to_representation(instance)
        data["articles"] = list(
            instance.articles.filter(approved=True)
            .values_list("pk", flat=True)
        )
        return data

    def validate_articles(self, articles):
        request = self.context.get("request")

        if request and request.user.role == User.Role.JOURNALIST:
            own_articles = set(
                request.user.articles.values_list("id", flat=True)
            )
            if any(article.id not in own_articles for article in articles):
                raise serializers.ValidationError(
                    "Journalists may only include their own articles."
                )

        return articles


class ApprovedArticleSerializer(serializers.ModelSerializer):
    """Validate the internal approval audit payload."""

    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    publisher = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Article
        fields = (
            "id",
            "title",
            "content",
            "author",
            "publisher",
            "approved",
            "created_at",
        )
        read_only_fields = ("id", "approved", "created_at")
