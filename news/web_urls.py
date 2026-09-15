from django.urls import path

from .views import approve_article, article_review

urlpatterns = [
    path(
        "articles/review/",
        article_review,
        name="article-review",
    ),
    path(
        "articles/<int:article_id>/approve/",
        approve_article,
        name="approve-article",
    ),
]
