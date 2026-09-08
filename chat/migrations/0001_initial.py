import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AnswerAudit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "request_id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                    ),
                ),
                (
                    "query_hmac",
                    models.CharField(
                        help_text="HMAC-SHA256 hex of query text",
                        max_length=64,
                    ),
                ),
                (
                    "query_hmac_key_id",
                    models.CharField(default="v1", max_length=32),
                ),
                (
                    "corpus_version",
                    models.CharField(default="none", max_length=16),
                ),
                (
                    "jurisdiction",
                    models.CharField(
                        choices=[
                            ("IN", "India"),
                            ("INT", "International"),
                            ("BOTH", "India + International"),
                        ],
                        default="IN",
                        max_length=8,
                    ),
                ),
                (
                    "language_code",
                    models.CharField(default="en", max_length=8),
                ),
                (
                    "outcome",
                    models.CharField(
                        choices=[
                            ("grounded", "Strong evidence"),
                            ("evidence_only", "Limited evidence"),
                            ("unable_to_answer", "Unable to answer from verified sources"),
                            ("out_of_scope", "Out of scope"),
                            ("conflict", "Conflicting sources"),
                            ("busy", "Service busy"),
                            ("unavailable", "Service unavailable"),
                            ("demo", "Demo mode placeholder"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "cited_chunk_ids",
                    models.JSONField(blank=True, default=list),
                ),
                (
                    "latency_ms",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "cancelled",
                    models.BooleanField(default=False),
                ),
                (
                    "demo_mode",
                    models.BooleanField(default=False),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
            ],
            options={
                "verbose_name": "Answer Audit",
                "verbose_name_plural": "Answer Audits",
                "db_table": "answer_audit",
                "ordering": ["-created_at"],
            },
        ),
    ]
