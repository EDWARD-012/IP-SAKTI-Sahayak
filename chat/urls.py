from __future__ import annotations

from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("",        views.chat_view, name="chat"),
    path("ask/",    views.ask,       name="ask"),
    path("cancel/", views.cancel,    name="cancel"),
    path("session-clear/", views.session_clear, name="session_clear"),
]
