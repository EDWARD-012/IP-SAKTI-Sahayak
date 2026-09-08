from __future__ import annotations

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("",                views.home,          name="home"),
    path("language/set/",   views.set_language,  name="set_language"),
    path("screen-reader/",  views.screen_reader, name="screen_reader"),
    path("privacy/",        views.privacy,       name="privacy"),
    path("terms/",          views.terms,         name="terms"),
    path("help/",           views.help_page,     name="help"),
    path("contact/",        views.contact,       name="contact"),
]
