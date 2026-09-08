"""
chat/models.py — AnswerAudit + Feedback

DPDP-aligned audit log. Never stores the raw question text.
Stores only a keyed HMAC fingerprint of the query.
"""
from __future__ import annotations

import uuid

from django.db import models


class AnswerAudit(models.Model):
    """Minimal audit record for each /assistant/ask/ request."""

    OUTCOME_CHOICES = [
        ("grounded",         "Strong evidence"),
        ("evidence_only",    "Limited evidence"),
        ("unable_to_answer", "Unable to answer from verified sources"),
        ("out_of_scope",     "Out of scope"),
        ("conflict",         "Conflicting sources"),
        ("busy",             "Service busy"),
        ("unavailable",      "Service unavailable"),
        ("demo",             "Demo mode placeholder"),
    ]

    JURISDICTION_CHOICES = [
        ("IN",   "India"),
        ("INT",  "International"),
        ("BOTH", "India + International"),
    ]

    request_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    # DPDP: never store raw query text
    query_hmac = models.CharField(max_length=64, help_text="HMAC-SHA256 hex of query text")
    query_hmac_key_id = models.CharField(max_length=32, default="v1")

    corpus_version = models.CharField(max_length=16, default="none")
    jurisdiction = models.CharField(max_length=8, choices=JURISDICTION_CHOICES, default="IN")
    language_code = models.CharField(max_length=8, default="en")

    outcome = models.CharField(max_length=32, choices=OUTCOME_CHOICES)
    cited_chunk_ids = models.JSONField(default=list, blank=True)

    latency_ms = models.IntegerField(null=True, blank=True)
    cancelled = models.BooleanField(default=False)
    demo_mode = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "answer_audit"
        ordering = ["-created_at"]
        verbose_name = "Answer Audit"
        verbose_name_plural = "Answer Audits"

    def __str__(self) -> str:
        return f"[{self.outcome}] {self.request_id} @ {self.created_at:%Y-%m-%d %H:%M}"


class Feedback(models.Model):
    """User thumbs-up / thumbs-down on an assistant answer."""

    RATING_CHOICES = [
        ("up", "Helpful"),
        ("down", "Not helpful"),
    ]

    request_id = models.UUIDField(db_index=True)
    rating = models.CharField(max_length=8, choices=RATING_CHOICES)
    category = models.CharField(max_length=64, blank=True, default="")
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_feedback"
        ordering = ["-created_at"]
        verbose_name = "Feedback"
        verbose_name_plural = "Feedback"

    def __str__(self) -> str:
        return f"{self.rating} @ {self.request_id}"
