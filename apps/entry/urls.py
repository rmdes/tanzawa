from django.urls import path
from indieweb.constants import MPostKinds

from . import views

urlpatterns = [
    path("article/create/", views.CreateArticleView.as_view(), name="article_create"),
    path(
        "article/<int:pk>/edit/", views.UpdateArticleView.as_view(), name="article_edit"
    ),
    path("article/<int:pk>/delete/", views.status_delete, name="article_delete"),
    path("status/create/", views.CreateStatusView.as_view(), name="status_create"),
    path("status/<int:pk>/", views.status_detail, name="status_detail"),
    path("status/<int:pk>/edit/", views.UpdateStatusView.as_view(), name="status_edit"),
    path("status/<int:pk>/delete/", views.status_delete, name="status_delete"),
    path(
        "posts/",
        views.TEntryListView.as_view(),
        name="posts",
    ),
    path("posts/<int:pk>", views.edit_post, name="post_edit"),
]
