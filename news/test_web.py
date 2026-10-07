"""Automated tests for the public web authentication flow."""

from django.test import TestCase
from django.urls import reverse

from .models import User


class RegistrationTests(TestCase):
    """Test registration and authentication behaviour."""

    def test_registration_page_is_available(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create your account")

    def test_reader_can_register_and_is_logged_in(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "reader1",
                "email": "reader@example.com",
                "first_name": "News",
                "last_name": "Reader",
                "role": User.Role.READER,
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
        )

        self.assertRedirects(response, reverse("home"))
        user = User.objects.get(username="reader1")
        self.assertEqual(user.role, User.Role.READER)
        self.assertTrue(user.is_authenticated)

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="existing",
            email="reader@example.com",
            password="StrongPassword123!",
        )

        response = self.client.post(
            reverse("register"),
            {
                "username": "new-reader",
                "email": "reader@example.com",
                "first_name": "New",
                "last_name": "Reader",
                "role": User.Role.READER,
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "An account with this email address already exists.",
        )

    def test_login_and_logout_work(self):
        User.objects.create_user(
            username="reader1",
            password="StrongPassword123!",
            role=User.Role.READER,
        )

        login_response = self.client.post(
            reverse("login"),
            {
                "username": "reader1",
                "password": "StrongPassword123!",
            },
        )
        self.assertRedirects(login_response, reverse("home"))

        logout_response = self.client.post(reverse("logout"))
        self.assertRedirects(logout_response, reverse("home"))
