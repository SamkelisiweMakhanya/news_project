"""Forms for the news application's web interface."""

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Article, Newsletter, Publisher, User


class RegistrationForm(UserCreationForm):
    """Register a user and assign an application role."""

    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.Role.choices)

    class Meta:
        model = User
        fields = (
            "username", "email", "first_name", "last_name", "role",
            "password1", "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email address already exists."
            )
        return email


class ArticleForm(forms.ModelForm):
    """Create or edit an article."""

    class Meta:
        model = Article
        fields = ("title", "content", "publisher")
        widgets = {"content": forms.Textarea(attrs={"rows": 10})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user and user.role == User.Role.JOURNALIST:
            self.fields["publisher"].queryset = Publisher.objects.filter(
                members=user
            )

    def clean(self):
        cleaned = super().clean()
        publisher = cleaned.get("publisher")
        if not self.user:
            raise forms.ValidationError("Authentication is required.")
        if self.user.role == User.Role.JOURNALIST and publisher:
            if not publisher.members.filter(pk=self.user.pk).exists():
                raise forms.ValidationError(
                    "You must be linked to a publisher before creating "
                    "publisher content."
                )
        if self.user.role == User.Role.EDITOR and self.instance.pk:
            return cleaned
        if self.user.role != User.Role.JOURNALIST:
            raise forms.ValidationError("You do not have article permissions.")
        return cleaned



class NewsletterForm(forms.ModelForm):
    """Create or edit a newsletter."""

    class Meta:
        model = Newsletter
        fields = ("title", "description", "articles")
        widgets = {"description": forms.Textarea(attrs={"rows": 6})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user and user.role == User.Role.JOURNALIST:
            self.fields["articles"].queryset = Article.objects.filter(
                author=user, approved=True
            )


class PublisherForm(forms.ModelForm):
    """Create or update a publisher."""

    class Meta:
        model = Publisher
        fields = ("name", "description", "members")
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["members"].queryset = User.objects.filter(
            role__in=(User.Role.JOURNALIST, User.Role.EDITOR)
        )
