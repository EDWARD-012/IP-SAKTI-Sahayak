from __future__ import annotations

from django.urls import path

from . import views

app_name = "corpus"

urlpatterns = [
    path("about/",   views.about_corpus,  name="about"),
    path("sources/", views.sources_list,  name="sources"),
]
