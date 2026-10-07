"""
Test suite for the news application's API and authentication features.

This module contains automated tests for article and newsletter APIs,
role-based permissions, publisher subscriptions, article approval,
email notifications, API logging, user groups, and token authentication.
"""

from unittest.mock import patch

import requests
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Article, Newsletter, Publisher

User = get_user_model()


class ArticleAPITests(APITestCase):
    """Test article API authentication, roles, and subscriptions."""

    def setUp(self):
        """Create users, publishers, and articles required by the tests."""
        self.reader = User.objects.create_user(
            username="reader1",
            password="ReaderPass123!",
            role=User.Role.READER,
        )
        self.journalist = User.objects.create_user(
            username="journalist1",
            password="JournalistPass123!",
            role=User.Role.JOURNALIST,
        )
        self.editor = User.objects.create_user(
            username="editor1",
            password="EditorPass123!",
            role=User.Role.EDITOR,
        )

        self.publisher = Publisher.objects.create(
            name="Test Publisher",
            description="Publisher used for automated tests.",
        )

        self.other_publisher = Publisher.objects.create(
            name="Other Publisher",
            description="A publisher the reader does not follow.",
        )

        self.publisher.members.add(self.journalist)

        self.reader.subscribed_publishers.add(
            self.publisher
        )

        self.subscribed_article = Article.objects.create(
            title="Subscribed Article",
            content="Visible to this reader.",
            author=self.journalist,
            publisher=self.publisher,
            approved=True,
        )

        self.unsubscribed_article = Article.objects.create(
            title="Unsubscribed Article",
            content="Not visible through subscriptions.",
            author=self.journalist,
            publisher=self.other_publisher,
            approved=True,
        )

        self.independent_article = Article.objects.create(
            title="Independent Article",
            content="Written independently.",
            author=self.journalist,
            approved=True,
        )

    def authenticate(self, user):
        """Authenticate the test client using a DRF token for the user."""
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    def test_unauthenticated_article_list_is_rejected(self):
        """Verify unauthenticated users cannot access the article API."""
        url = reverse("article-list-create")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 401)

    def test_reader_can_retrieve_approved_articles(self):
        """Verify readers can retrieve approved articles."""
        self.authenticate(self.reader)

        url = reverse("article-list-create")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        returned_titles = {
            article["title"]
            for article in response.data
        }

        self.assertIn(
            "Subscribed Article",
            returned_titles,
        )

        self.assertIn(
            "Unsubscribed Article",
            returned_titles,
        )

    def test_reader_can_only_retrieve_subscribed_articles(self):
        """Verify readers only receive articles from subscribed publishers."""
        self.authenticate(self.reader)

        url = reverse("subscribed-articles")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        returned_titles = {
            article["title"]
            for article in response.data
        }

        self.assertIn(
            "Subscribed Article",
            returned_titles,
        )

        self.assertNotIn(
            "Unsubscribed Article",
            returned_titles,
        )

        self.assertNotIn(
            "Independent Article",
            returned_titles,
        )

    def test_reader_cannot_create_article(self):
        """Verify readers are not permitted to create articles."""
        self.authenticate(self.reader)

        url = reverse("article-list-create")

        response = self.client.post(
            url,
            {
                "title": "Reader Article",
                "content": "Readers cannot create articles.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_journalist_can_create_article(self):
        """Verify journalists can create new articles."""
        self.authenticate(self.journalist)

        url = reverse("article-list-create")

        response = self.client.post(
            url,
            {
                "title": "New Journalist Article",
                "content": "Created by a journalist.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["title"],
            "New Journalist Article",
        )

    def test_journalist_can_update_article(self):
        """Verify journalists can update an existing article."""
        self.authenticate(self.journalist)

        url = reverse(
            "article-detail",
            kwargs={"pk": self.independent_article.pk},
        )

        response = self.client.put(
            url,
            {
                "title": "Updated Article",
                "content": "Updated content.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["title"],
            "Updated Article",
        )

    def test_editor_can_delete_article(self):
        """Verify editors can delete an existing article."""
        self.authenticate(self.editor)

        url = reverse(
            "article-detail",
            kwargs={"pk": self.independent_article.pk},
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Article.objects.filter(
                pk=self.independent_article.pk
            ).exists()
        )

    def test_editor_cannot_create_article(self):
        """Verify editors cannot create articles."""
        self.authenticate(self.editor)

        response = self.client.post(
            reverse("article-list-create"),
            {
                "title": "Editor Article",
                "content": "Editors cannot create articles.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_reader_cannot_update_article(self):
        """Verify readers cannot update articles."""
        self.authenticate(self.reader)

        url = reverse(
            "article-detail",
            kwargs={"pk": self.subscribed_article.pk},
        )

        response = self.client.put(
            url,
            {
                "title": "Reader Update",
                "content": "Readers cannot update articles.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_reader_cannot_delete_article(self):
        """Verify readers cannot delete articles."""
        self.authenticate(self.reader)

        url = reverse(
            "article-detail",
            kwargs={"pk": self.subscribed_article.pk},
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            Article.objects.filter(
                pk=self.subscribed_article.pk
            ).exists()
        )

    def test_journalist_cannot_update_another_journalists_article(self):
        """Verify journalists cannot update another journalist's article."""
        other_journalist = User.objects.create_user(
            username="other_journalist",
            password="OtherJournalistPass123!",
            role=User.Role.JOURNALIST,
        )

        article = Article.objects.create(
            title="Other Journalist Article",
            content="Owned by another journalist.",
            author=other_journalist,
            approved=True,
        )

        self.authenticate(self.journalist)

        response = self.client.put(
            reverse(
                "article-detail",
                kwargs={"pk": article.pk},
            ),
            {
                "title": "Unauthorized Update",
                "content": "This update should fail.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        article.refresh_from_db()

        self.assertEqual(
            article.title,
            "Other Journalist Article",
        )

    def test_journalist_cannot_delete_another_journalists_article(self):
        """Verify journalists cannot delete another journalist's article."""
        other_journalist = User.objects.create_user(
            username="delete_other_journalist",
            password="OtherJournalistPass123!",
            role=User.Role.JOURNALIST,
        )

        article = Article.objects.create(
            title="Protected Article",
            content="Owned by another journalist.",
            author=other_journalist,
            approved=True,
        )

        self.authenticate(self.journalist)

        response = self.client.delete(
            reverse(
                "article-detail",
                kwargs={"pk": article.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            Article.objects.filter(pk=article.pk).exists()
        )

    def test_journalist_update_resets_approval(self):
        """Verify journalist edits require the article to be re-approved."""
        self.authenticate(self.journalist)

        response = self.client.put(
            reverse(
                "article-detail",
                kwargs={"pk": self.independent_article.pk},
            ),
            {
                "title": "Updated Independent Article",
                "content": "Updated content requiring approval.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.independent_article.refresh_from_db()

        self.assertFalse(self.independent_article.approved)

    def test_reader_can_receive_articles_from_subscribed_journalist(self):
        """Verify readers receive articles from subscribed journalists."""
        other_journalist = User.objects.create_user(
            username="unsubscribed_journalist",
            password="OtherJournalistPass123!",
            role=User.Role.JOURNALIST,
        )

        Article.objects.create(
            title="Other Journalist Article",
            content="Written by an unsubscribed journalist.",
            author=other_journalist,
            approved=True,
        )

        self.reader.subscribed_publishers.clear()
        self.reader.subscribed_journalists.add(self.journalist)

        self.authenticate(self.reader)

        response = self.client.get(
            reverse("subscribed-articles")
        )

        self.assertEqual(response.status_code, 200)

        returned_titles = {
            article["title"]
            for article in response.data
        }

        self.assertIn(
            "Independent Article",
            returned_titles,
        )

        self.assertIn(
            "Subscribed Article",
            returned_titles,
        )

        self.assertNotIn(
            "Other Journalist Article",
            returned_titles,
        )

    def test_journalist_cannot_create_article_with_invalid_publisher(self):
        """Verify journalists cannot submit an invalid publisher."""
        self.authenticate(self.journalist)

        response = self.client.post(
            reverse("article-list-create"),
            {
                "title": "Invalid Publisher Article",
                "content": "This should fail validation.",
                "publisher": 999999,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)


class NewsletterAPITests(APITestCase):
    """Test newsletter permissions and API behavior."""

    def setUp(self):
        """Create users, an article, and a newsletter for testing."""
        self.reader = User.objects.create_user(
            username="newsletter_reader",
            password="ReaderPass123!",
            role=User.Role.READER,
        )

        self.journalist = User.objects.create_user(
            username="newsletter_journalist",
            password="JournalistPass123!",
            role=User.Role.JOURNALIST,
        )

        self.editor = User.objects.create_user(
            username="newsletter_editor",
            password="EditorPass123!",
            role=User.Role.EDITOR,
        )

        self.article = Article.objects.create(
            title="Newsletter Article",
            content="Article content.",
            author=self.journalist,
            approved=True,
        )

        self.newsletter = Newsletter.objects.create(
            title="Weekly News",
            description="Weekly newsletter.",
            author=self.journalist,
        )

        self.newsletter.articles.add(self.article)

    def authenticate(self, user):
        """Authenticate the test client using a DRF token for the user."""
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    def test_journalist_cannot_create_newsletter_with_invalid_article(
        self,
    ):
        """Verify invalid article references are rejected."""
        self.authenticate(self.journalist)

        response = self.client.post(
            reverse("newsletter-list-create"),
            {
                "title": "Invalid Newsletter",
                "description": "This should fail validation.",
                "articles": [999999],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_reader_can_view_newsletters(self):
        """Verify readers can view available newsletters."""
        self.authenticate(self.reader)

        response = self.client.get(
            reverse("newsletter-list-create")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["title"],
            "Weekly News",
        )

    def test_reader_cannot_create_newsletter(self):
        """Verify readers cannot create newsletters."""
        self.authenticate(self.reader)

        response = self.client.post(
            reverse("newsletter-list-create"),
            {
                "title": "Reader Newsletter",
                "description": "Not allowed.",
                "articles": [self.article.pk],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_journalist_can_create_newsletter(self):
        """Verify journalists can create newsletters."""
        self.authenticate(self.journalist)

        response = self.client.post(
            reverse("newsletter-list-create"),
            {
                "title": "Journalist Newsletter",
                "description": "Created by journalist.",
                "articles": [self.article.pk],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["author"]["username"],
            "newsletter_journalist",
        )

    def test_editor_can_create_newsletter(self):
        """Verify editors can create newsletters."""
        self.authenticate(self.editor)

        response = self.client.post(
            reverse("newsletter-list-create"),
            {
                "title": "Editor Newsletter",
                "description": "Created by editor.",
                "articles": [self.article.pk],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

    def test_editor_can_delete_newsletter(self):
        """Verify editors can delete newsletters."""
        self.authenticate(self.editor)

        response = self.client.delete(
            reverse(
                "newsletter-detail",
                kwargs={"pk": self.newsletter.pk},
            )
        )

        self.assertEqual(response.status_code, 204)

    def test_unauthenticated_user_cannot_view_newsletters(self):
        """Verify unauthenticated users cannot view newsletters."""
        response = self.client.get(
            reverse("newsletter-list-create")
        )

        self.assertEqual(response.status_code, 401)

    def test_reader_cannot_update_newsletter(self):
        """Verify readers cannot update newsletters."""
        self.authenticate(self.reader)

        response = self.client.put(
            reverse(
                "newsletter-detail",
                kwargs={"pk": self.newsletter.pk},
            ),
            {
                "title": "Reader Update",
                "description": "Readers cannot update newsletters.",
                "articles": [self.article.pk],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_reader_cannot_delete_newsletter(self):
        """Verify readers cannot delete newsletters."""
        self.authenticate(self.reader)

        response = self.client.delete(
            reverse(
                "newsletter-detail",
                kwargs={"pk": self.newsletter.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            Newsletter.objects.filter(
                pk=self.newsletter.pk
            ).exists()
        )

    def test_journalist_can_update_own_newsletter(self):
        """Verify journalists can update their own newsletters."""
        self.authenticate(self.journalist)

        response = self.client.put(
            reverse(
                "newsletter-detail",
                kwargs={"pk": self.newsletter.pk},
            ),
            {
                "title": "Updated Weekly News",
                "description": "Updated newsletter.",
                "articles": [self.article.pk],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.newsletter.refresh_from_db()

        self.assertEqual(
            self.newsletter.title,
            "Updated Weekly News",
        )

    def test_journalist_cannot_update_another_journalists_newsletter(
        self,
    ):
        """Verify journalists cannot update another journalist's newsletter."""
        other_journalist = User.objects.create_user(
            username="other_newsletter_journalist",
            password="OtherJournalistPass123!",
            role=User.Role.JOURNALIST,
        )

        other_newsletter = Newsletter.objects.create(
            title="Protected Newsletter",
            description="Owned by another journalist.",
            author=other_journalist,
        )

        self.authenticate(self.journalist)

        response = self.client.put(
            reverse(
                "newsletter-detail",
                kwargs={"pk": other_newsletter.pk},
            ),
            {
                "title": "Unauthorized Update",
                "description": "This update should fail.",
                "articles": [self.article.pk],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        other_newsletter.refresh_from_db()

        self.assertEqual(
            other_newsletter.title,
            "Protected Newsletter",
        )

    def test_journalist_cannot_delete_another_journalists_newsletter(
        self,
    ):
        """Verify journalists cannot delete another journalist's newsletter."""
        other_journalist = User.objects.create_user(
            username="delete_newsletter_journalist",
            password="OtherJournalistPass123!",
            role=User.Role.JOURNALIST,
        )

        other_newsletter = Newsletter.objects.create(
            title="Protected Newsletter",
            description="Owned by another journalist.",
            author=other_journalist,
        )

        self.authenticate(self.journalist)

        response = self.client.delete(
            reverse(
                "newsletter-detail",
                kwargs={"pk": other_newsletter.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            Newsletter.objects.filter(
                pk=other_newsletter.pk
            ).exists()
        )


class ApprovalWorkflowTests(APITestCase):
    """Test editor approval, email notification, and API logging."""

    def setUp(self):
        """Create users, a publisher, and an unapproved article."""
        self.reader = User.objects.create_user(
            username="approval_reader",
            password="ReaderPass123!",
            email="reader@example.com",
            role=User.Role.READER,
        )

        self.journalist = User.objects.create_user(
            username="approval_journalist",
            password="JournalistPass123!",
            email="journalist@example.com",
            role=User.Role.JOURNALIST,
        )

        self.editor = User.objects.create_user(
            username="approval_editor",
            password="EditorPass123!",
            role=User.Role.EDITOR,
        )

        self.publisher = Publisher.objects.create(
            name="Approval Publisher",
            description="Publisher for approval tests.",
        )

        self.publisher.members.add(self.journalist)
        self.reader.subscribed_publishers.add(self.publisher)

        self.article = Article.objects.create(
            title="Article Awaiting Approval",
            content="Content awaiting editor approval.",
            author=self.journalist,
            publisher=self.publisher,
            approved=False,
        )

    def authenticate(self, user):
        """Authenticate the test client as the specified user."""
        self.client.force_login(user)

    @patch("news.views.requests.post")
    @patch("news.views.send_mail")
    def test_editor_can_approve_article(
        self,
        mock_send_mail,
        mock_post,
    ):
        """Verify editors can approve articles and trigger notifications."""
        self.authenticate(self.editor)

        response = self.client.post(
            reverse(
                "approve-article",
                kwargs={"article_id": self.article.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.article.refresh_from_db()

        self.assertTrue(self.article.approved)

        mock_send_mail.assert_called_once()

        mock_post.assert_called_once()

        request_json = mock_post.call_args.kwargs["json"]

        self.assertEqual(
            request_json["id"],
            self.article.id,
        )

        self.assertTrue(
            request_json["approved"]
        )

    @patch("news.views.requests.post")
    @patch("news.views.send_mail")
    def test_approved_article_email_goes_to_subscribers(
        self,
        mock_send_mail,
        mock_post,
    ):
        """Verify approved article notifications are sent to subscribers."""
        self.authenticate(self.editor)

        self.client.post(
            reverse(
                "approve-article",
                kwargs={"article_id": self.article.pk},
            )
        )

        email_call = mock_send_mail.call_args

        recipient_list = email_call.kwargs["recipient_list"]

        self.assertIn(
            "reader@example.com",
            recipient_list,
        )

    def test_reader_cannot_approve_article(self):
        """Verify readers cannot approve articles."""
        self.authenticate(self.reader)

        response = self.client.post(
            reverse(
                "approve-article",
                kwargs={"article_id": self.article.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

        self.article.refresh_from_db()

        self.assertFalse(self.article.approved)

    def test_journalist_cannot_approve_article(self):
        """Verify journalists cannot approve articles."""
        self.authenticate(self.journalist)

        response = self.client.post(
            reverse(
                "approve-article",
                kwargs={"article_id": self.article.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

        self.article.refresh_from_db()

        self.assertFalse(self.article.approved)

    @patch("news.api_views.ApprovedArticleSerializer")
    def test_approved_api_endpoint_accepts_post(
        self,
        mock_serializer_class,
    ):
        """Verify the approved article API endpoint accepts valid POST data."""
        mock_serializer = mock_serializer_class.return_value
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {
            "id": self.article.id,
            "title": self.article.title,
            "content": self.article.content,
            "author": self.journalist.id,
            "publisher": self.publisher.id,
            "approved": True,
        }

        response = self.client.post(
            reverse("approved-article"),
            {
                "id": self.article.id,
                "title": self.article.title,
                "content": self.article.content,
                "author": self.journalist.id,
                "publisher": self.publisher.id,
                "approved": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

    @patch("news.views.requests.post")
    @patch("news.views.send_mail")
    def test_independent_article_notifies_journalist_subscribers(
        self,
        mock_send_mail,
        mock_post,
    ):
        """Verify independent articles notify journalist subscribers."""
        self.reader.subscribed_publishers.clear()
        self.reader.subscribed_journalists.add(self.journalist)

        independent_article = Article.objects.create(
            title="Independent Article Awaiting Approval",
            content="Independent journalist content.",
            author=self.journalist,
            approved=False,
        )

        self.authenticate(self.editor)

        response = self.client.post(
            reverse(
                "approve-article",
                kwargs={"article_id": independent_article.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        independent_article.refresh_from_db()

        self.assertTrue(independent_article.approved)
        mock_send_mail.assert_called_once()

        recipient_list = mock_send_mail.call_args.kwargs[
            "recipient_list"
        ]

        self.assertIn(
            "reader@example.com",
            recipient_list,
        )

    @patch(
        "news.views.requests.post",
        side_effect=requests.RequestException(
            "API connection failed"
        ),
    )
    @patch("news.views.send_mail")
    def test_approval_succeeds_when_internal_api_fails(
        self,
        mock_send_mail,
        mock_post,
    ):
        """Verify article approval survives an internal API failure."""
        self.authenticate(self.editor)

        response = self.client.post(
            reverse(
                "approve-article",
                kwargs={"article_id": self.article.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.article.refresh_from_db()

        self.assertTrue(self.article.approved)
        mock_send_mail.assert_called_once()
        mock_post.assert_called_once()

    @patch("news.views.requests.post")
    @patch("news.views.send_mail")
    def test_already_approved_article_cannot_be_approved_again(
        self,
        mock_send_mail,
        mock_post,
    ):
        """Verify already-approved articles are not approved again."""
        self.article.approved = True
        self.article.save()

        self.authenticate(self.editor)

        response = self.client.post(
            reverse(
                "approve-article",
                kwargs={"article_id": self.article.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

        mock_send_mail.assert_not_called()
        mock_post.assert_not_called()

    def test_unauthenticated_user_cannot_approve_article(self):
        """Verify unauthenticated users cannot approve articles."""
        response = self.client.post(
            reverse(
                "approve-article",
                kwargs={"article_id": self.article.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.article.refresh_from_db()

        self.assertFalse(self.article.approved)


class RoleAndAuthenticationTests(APITestCase):
    """Test role-based groups and token authentication."""

    def test_reader_is_assigned_reader_group(self):
        """Verify readers are automatically assigned to the
        Reader group.
        """
        reader = User.objects.create_user(
            username="group_reader",
            password="ReaderPass123!",
            role=User.Role.READER,
        )

        self.assertTrue(
            reader.groups.filter(name="Reader").exists()
        )

    def test_journalist_is_assigned_journalist_group(self):
        """Verify journalists are automatically assigned to the
        Journalist group.
        """
        journalist = User.objects.create_user(
            username="group_journalist",
            password="JournalistPass123!",
            role=User.Role.JOURNALIST,
        )

        self.assertTrue(
            journalist.groups.filter(name="Journalist").exists()
        )

    def test_editor_is_assigned_editor_group(self):
        """Verify editors are automatically assigned to the
        Editor group.
        """
        editor = User.objects.create_user(
            username="group_editor",
            password="EditorPass123!",
            role=User.Role.EDITOR,
        )

        self.assertTrue(
            editor.groups.filter(name="Editor").exists()
        )

    def test_token_endpoint_authenticates_user(self):
        """Verify valid credentials return an
        authentication token.
        """
        user = User.objects.create_user(
            username="token_user",
            password="TokenPass123!",
            role=User.Role.READER,
        )

        response = self.client.post(
            "/api/token/",
            {
                "username": user.username,
                "password": "TokenPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)

    def test_invalid_token_credentials_are_rejected(self):
        """Verify invalid credentials are rejected by the
        token endpoint.
        """
        response = self.client.post(
            "/api/token/",
            {
                "username": "does_not_exist",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
