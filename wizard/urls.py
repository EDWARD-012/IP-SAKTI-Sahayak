from __future__ import annotations

from django.urls import path

from . import views

app_name = "wizard"

urlpatterns = [
    path("",        views.wizard_start,  name="start"),
    path("step/",   views.wizard_step,   name="step"),
    path("result/", views.wizard_result, name="result"),
    path("reset/",  views.wizard_reset,  name="reset"),
]
