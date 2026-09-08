"""
corpus/models.py — CorpusVersion
Tracks the lifecycle of each Chroma vector index built from legal documents.
"""
from __future__ import annotations

from django.db import models
from django.utils import timezone


class CorpusVersion(models.Model):
    """
    Lifecycle: building → validated → active → retired | failed
    Only ONE version may be active at a time.
    """

    STATUS_CHOICES = [
        ("building",  "Building"),
        ("validated", "Validated"),
        ("active",    "Active"),
        ("retired",   "Retired"),
        ("failed",    "Failed"),
    ]

    version = models.CharField(max_length=16, unique=True, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="building")
    chroma_collection = models.CharField(
        max_length=64,
        help_text="Chroma collection name, e.g. ip_sakti_v1",
    )
    sources_count = models.IntegerField(default=0)
    chunks_count = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    retired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "corpus_version"
        ordering = ["-created_at"]
        verbose_name = "Corpus Version"
        verbose_name_plural = "Corpus Versions"

    def __str__(self) -> str:
        return f"v{self.version} [{self.status}] — {self.chunks_count} chunks"

    def activate(self) -> None:
        """Mark this version active; retire all others."""
        CorpusVersion.objects.exclude(pk=self.pk).filter(status="active").update(
            status="retired",
            retired_at=timezone.now(),
        )
        self.status = "active"
        self.activated_at = timezone.now()
        self.save(update_fields=["status", "activated_at"])


class SourceManifest(models.Model):
    """
    Tracks individual source documents in the corpus.
    Mirrors the YAML manifests in data/manifests/.
    """

    REUSE_CHOICES = [
        ("public-statute",    "Public Statute"),
        ("official-open",     "Official Open"),
        ("verify-and-record", "Verify and Record"),
    ]

    STATUS_CHOICES = [
        ("current",              "Current"),
        ("amended",              "Amended"),
        ("repealed",             "Repealed"),
        ("draft",                "Draft"),
        ("signed-not-in-force",  "Signed — Not in Force"),
    ]

    source_id = models.CharField(max_length=64, unique=True, db_index=True)
    title = models.CharField(max_length=256)
    authority = models.CharField(max_length=128)
    jurisdiction = models.CharField(max_length=8, default="IN")
    ip_types = models.JSONField(default=list)
    landing_url = models.URLField(blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="current")
    reuse_basis = models.CharField(max_length=32, choices=REUSE_CHOICES, default="public-statute")
    retrieved_at = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    corpus_version = models.ForeignKey(
        CorpusVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sources",
    )

    class Meta:
        db_table = "source_manifest"
        ordering = ["source_id"]

    def __str__(self) -> str:
        return f"{self.source_id} — {self.title}"
