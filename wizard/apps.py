from __future__ import annotations

from django.apps import AppConfig


class WizardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wizard"
    verbose_name = "IP-SAKTI Formulation Wizard"
