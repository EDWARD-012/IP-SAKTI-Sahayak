"""
IP-SAKTI Sahayak — Root URL Configuration
"""
from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("",           include("core.urls",   namespace="core")),
    path("assistant/", include("chat.urls",   namespace="chat")),
    path("corpus/",    include("corpus.urls", namespace="corpus")),
    path("wizard/",    include("wizard.urls", namespace="wizard")),
]
