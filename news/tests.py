from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Article, Newsletter, Publisher

User = get_user_model()


class ArticleAPITests(APITestCase):
    """Test article API authentication, roles, and subscriptions."""

    def setUp(self):
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
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    def test_unauthenticated_article_list_is_rejected(self):
        url = reverse("article-list-create")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 401)

    def test_reader_can_retrieve_approved_articles(self):
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


class NewsletterAPITests(APITestCase):
    """Test newsletter permissions and API behavior."""

    def setUp(self):
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
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    def test_reader_can_view_newsletters(self):
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
        self.authenticate(self.editor)

        response = self.client.delete(
            reverse(
                "newsletter-detail",
                kwargs={"pk": self.newsletter.pk},
            )
        )

        self.assertEqual(response.status_code, 204)

    def test_unauthenticated_user_cannot_view_newsletters(self):
        response = self.client.get(
            reverse("newsletter-list-create")
        )

        self.assertEqual(response.status_code, 401)


class ApprovalWorkflowTests(APITestCase):
    """Test editor approval, email notification, and API logging."""

    def setUp(self):
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
        self.client.force_login(user)

    @patch("news.views.requests.post")
    @patch("news.views.send_mail")
    def test_editor_can_approve_article(
        self,
        mock_send_mail,
        mock_post,
    ):
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


class RoleAndAuthenticationTests(APITestCase):
    """Test role-based groups and token authentication."""

    def test_reader_is_assigned_reader_group(self):
        reader = User.objects.create_user(
            username="group_reader",
            password="ReaderPass123!",
            role=User.Role.READER,
        )

        self.assertTrue(
            reader.groups.filter(name="Reader").exists()
        )

    def test_journalist_is_assigned_journalist_group(self):
        journalist = User.objects.create_user(
            username="group_journalist",
            password="JournalistPass123!",
            role=User.Role.JOURNALIST,
        )

        self.assertTrue(
            journalist.groups.filter(name="Journalist").exists()
        )

    def test_editor_is_assigned_editor_group(self):
        editor = User.objects.create_user(
            username="group_editor",
            password="EditorPass123!",
            role=User.Role.EDITOR,
        )

        self.assertTrue(
            editor.groups.filter(name="Editor").exists()
        )

    def test_token_endpoint_authenticates_user(self):
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
        response = self.client.post(
            "/api/token/",
            {
                "username": "does_not_exist",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
