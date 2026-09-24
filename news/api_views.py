"""
API views for the news application.

This module defines API views and permission classes for managing
articles and newsletters. It handles authentication, role-based
permissions, article subscriptions, article approval, and newsletter
management.
"""

from typing import ClassVar

from rest_framework import generics, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article, Newsletter
from .serializers import (
    ApprovedArticleSerializer,
    ArticleSerializer,
    NewsletterSerializer,
)


class IsEditorOrJournalist(permissions.BasePermission):
    """Allow changes only to editors and journalists."""

    def has_permission(self, request, view):
        """Check whether the authenticated user is an editor or journalist."""
        return (
            request.user.is_authenticated
            and request.user.role
            in (
                request.user.Role.EDITOR,
                request.user.Role.JOURNALIST,
            )
        )


class IsJournalist(permissions.BasePermission):
    """Allow article creation only to journalists."""

    def has_permission(self, request, view):
        """Check whether the authenticated user is a journalist."""
        return (
            request.user.is_authenticated
            and request.user.role == request.user.Role.JOURNALIST
        )


class ArticleListCreateView(generics.ListCreateAPIView):
    """List visible articles and allow journalists to create articles."""

    serializer_class = ArticleSerializer

    def get_queryset(self):
        """Return articles visible to the current user's role."""
        queryset = Article.objects.all().select_related(
            "author",
            "publisher",
        )

        if self.request.user.role == self.request.user.Role.READER:
            return queryset.filter(approved=True)

        return queryset

    def get_permissions(self):
        """Return permissions based on the HTTP request method."""
        if self.request.method == "POST":
            return [IsJournalist()]

        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        """Save a new article with the authenticated user as its author."""
        serializer.save(author=self.request.user)


class SubscribedArticlesView(APIView):
    """Return approved articles from a reader's subscriptions."""

    permission_classes: ClassVar[list] = [permissions.IsAuthenticated]

    def get(self, request):
        """Return approved articles from subscribed publishers or journalists.
        """
        if request.user.role != request.user.Role.READER:
            return Response(
                {
                    "detail": (
                        "Only readers can access subscribed articles."
                    )
                },
                status=403,
            )

        articles = (
            Article.objects.filter(
                approved=True,
                publisher__in=request.user.subscribed_publishers.all(),
            )
            | Article.objects.filter(
                approved=True,
                author__in=request.user.subscribed_journalists.all(),
            )
        )

        articles = articles.select_related(
            "author",
            "publisher",
        ).distinct()

        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)


class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an article."""

    serializer_class = ArticleSerializer

    def get_queryset(self):
        """Return articles available to the current user's role."""
        queryset = Article.objects.all().select_related(
            "author",
            "publisher",
        )

        if self.request.user.role == self.request.user.Role.READER:
            return queryset.filter(approved=True)

        return queryset

    def get_permissions(self):
        """Return permissions based on the HTTP request method."""
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsEditorOrJournalist()]

        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        """Save the updated article."""
        serializer.save()


class ApprovedArticleView(APIView):
    """Receive and log an approved article."""

    permission_classes: ClassVar[list] = [AllowAny]

    def post(self, request):
        """Validate an approved article and return the serialized data."""
        serializer = ApprovedArticleSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=400,
            )

        return Response(
            {
                "message": "Approved article received successfully.",
                "article": serializer.data,
            },
            status=201,
        )


class NewsletterListCreateView(generics.ListCreateAPIView):
    """List newsletters and allow journalists to create them."""

    serializer_class = NewsletterSerializer

    def get_queryset(self):
        """Return all newsletters with related authors and articles loaded."""
        return Newsletter.objects.all().select_related(
            "author",
        ).prefetch_related(
            "articles",
        )

    def get_permissions(self):
        """Return permissions based on the HTTP request method."""
        if self.request.method == "POST":
            return [IsEditorOrJournalist()]

        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        """Save a new newsletter with the authenticated user as its author."""
        serializer.save(author=self.request.user)


class NewsletterDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a newsletter."""

    serializer_class = NewsletterSerializer

    def get_queryset(self):
        """Return all newsletters with related authors and articles loaded."""
        return Newsletter.objects.all().select_related(
            "author",
        ).prefetch_related(
            "articles",
        )

    def get_permissions(self):
        """Return permissions based on the HTTP request method."""
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsEditorOrJournalist()]

        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        """Save the updated newsletter."""
        serializer.save()
