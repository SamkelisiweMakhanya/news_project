"""Forms for the news application's web interface."""

from typing import ClassVar

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Article, Newsletter, Publisher

User = get_user_model()


class RegistrationForm(UserCreationForm):
    """Register a new reader account."""

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email address already exists."
            )

        return email

    def save(self, commit=True):
        """Ensure public registration always creates a reader."""
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = User.Role.READER

        if commit:
            user.save()
            self.save_m2m()

        return user


class ArticleForm(forms.ModelForm):
    """Create or edit an article."""

    class Meta:
        model = Article
        fields = ("title", "content", "publisher")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        self.fields["content"].widget.attrs.update({"rows": 10})

        if user and user.role == User.Role.JOURNALIST:
            self.fields["publisher"].queryset = (
                Publisher.objects.filter(members=user)
            )

    def clean(self):
        cleaned = super().clean()
        publisher = cleaned.get("publisher")

        if not self.user:
            raise forms.ValidationError(
                "Authentication is required."
            )

        if (
            self.user.role == User.Role.JOURNALIST
            and publisher
            and not publisher.members.filter(
                pk=self.user.pk
            ).exists()
        ):
            raise forms.ValidationError(
                "You must be linked to a publisher before "
                "creating publisher content."
            )

        if (
            self.user.role == User.Role.EDITOR
            and self.instance.pk
        ):
            return cleaned

        if self.user.role != User.Role.JOURNALIST:
            raise forms.ValidationError(
                "You do not have article permissions."
            )

        return cleaned


class NewsletterForm(forms.ModelForm):
    """Create or edit a newsletter using approved articles only."""

    class Meta:
        model = Newsletter
        fields = ("title", "description", "articles")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        self.fields["description"].widget.attrs["rows"] = 6

        approved_articles = Article.objects.filter(approved=True)

        if user and user.role == User.Role.JOURNALIST:
            approved_articles = approved_articles.filter(author=user)

        self.fields["articles"].queryset = approved_articles.order_by(
            "-created_at"
        )


class PublisherForm(forms.ModelForm):
    """Create or update a publisher and assign its staff."""

    editors = forms.ModelMultipleChoiceField(
        label="Editors",
        queryset=User.objects.none(),
        required=True,
        help_text="Select at least one editor.",
    )

    journalists = forms.ModelMultipleChoiceField(
        label="Journalists",
        queryset=User.objects.none(),
        required=True,
        help_text="Select at least one journalist.",
    )

    class Meta:
        model = Publisher
        fields = ("name", "description")
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["editors"].queryset = User.objects.filter(
            role=User.Role.EDITOR,
            is_active=True,
        ).order_by("username")

        self.fields["journalists"].queryset = User.objects.filter(
            role=User.Role.JOURNALIST,
            is_active=True,
        ).order_by("username")

        if self.instance and self.instance.pk:
            members = self.instance.members.all()

            self.initial["editors"] = members.filter(
                role=User.Role.EDITOR
            )

            self.initial["journalists"] = members.filter(
                role=User.Role.JOURNALIST
            )

    def save(self, commit=True):
        """Save the publisher and its selected staff members."""
        publisher = super().save(commit=commit)

        if commit:
            self._save_members()

        return publisher

    def _save_members(self):
        """Store editors and journalists in the existing members field."""
        editors = self.cleaned_data["editors"]
        journalists = self.cleaned_data["journalists"]

        self.instance.members.set(
            list(editors) + list(journalists)
        )
