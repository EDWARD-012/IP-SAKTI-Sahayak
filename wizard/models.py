"""
wizard/models.py — WizardSession
Stores formulation wizard progress (expires after 24 hours).
"""
from __future__ import annotations

import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone


def _default_expires() -> "timezone.datetime":
    return timezone.now() + timedelta(hours=24)


class WizardSession(models.Model):
    """
    One row per wizard session. Expires after 24 h (or on explicit reset).
    Answers are stored as a JSON dict: {step_key: answer_value}.
    """

    session_key = models.CharField(max_length=64, unique=True, db_index=True)
    idempotency_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    current_step = models.IntegerField(default=1)
    answers = models.JSONField(default=dict, blank=True)
    completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(default=_default_expires)

    class Meta:
        db_table = "wizard_session"
        ordering = ["-updated_at"]
        verbose_name = "Wizard Session"
        verbose_name_plural = "Wizard Sessions"

    def __str__(self) -> str:
        return f"WizardSession {self.session_key[:8]}… step={self.current_step}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def reset(self) -> None:
        self.current_step = 1
        self.answers = {}
        self.completed = False
        self.expires_at = _default_expires()
        self.idempotency_token = uuid.uuid4()
        self.save()
