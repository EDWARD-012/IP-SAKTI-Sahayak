import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CorpusVersion",
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
                    "version",
                    models.CharField(db_index=True, max_length=16, unique=True),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("building", "Building"),
                            ("validated", "Validated"),
                            ("active", "Active"),
                            ("retired", "Retired"),
                            ("failed", "Failed"),
                        ],
                        default="building",
                        max_length=16,
                    ),
                ),
                (
                    "chroma_collection",
                    models.CharField(
                        help_text="Chroma collection name, e.g. ip_sakti_v1",
                        max_length=64,
                    ),
                ),
                (
                    "sources_count",
                    models.IntegerField(default=0),
                ),
                (
                    "chunks_count",
                    models.IntegerField(default=0),
                ),
                (
                    "notes",
                    models.TextField(blank=True),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "activated_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "retired_at",
                    models.DateTimeField(blank=True, null=True),
                ),
            ],
            options={
                "verbose_name": "Corpus Version",
                "verbose_name_plural": "Corpus Versions",
                "db_table": "corpus_version",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="SourceManifest",
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
                    "source_id",
                    models.CharField(db_index=True, max_length=64, unique=True),
                ),
                (
                    "title",
                    models.CharField(max_length=256),
                ),
                (
                    "authority",
                    models.CharField(max_length=128),
                ),
                (
                    "jurisdiction",
                    models.CharField(default="IN", max_length=8),
                ),
                (
                    "ip_types",
                    models.JSONField(default=list),
                ),
                (
                    "landing_url",
                    models.URLField(blank=True),
                ),
                (
                    "sha256",
                    models.CharField(blank=True, max_length=64),
                ),
                (
                    "effective_from",
                    models.DateField(blank=True, null=True),
                ),
                (
                    "effective_status",
                    models.CharField(
                        choices=[
                            ("current", "Current"),
                            ("amended", "Amended"),
                            ("repealed", "Repealed"),
                            ("draft", "Draft"),
                            ("signed-not-in-force", "Signed \u2014 Not in Force"),
                        ],
                        default="current",
                        max_length=32,
                    ),
                ),
                (
                    "reuse_basis",
                    models.CharField(
                        choices=[
                            ("public-statute", "Public Statute"),
                            ("official-open", "Official Open"),
                            ("verify-and-record", "Verify and Record"),
                        ],
                        default="public-statute",
                        max_length=32,
                    ),
                ),
                (
                    "retrieved_at",
                    models.DateField(blank=True, null=True),
                ),
                (
                    "notes",
                    models.TextField(blank=True),
                ),
                (
                    "corpus_version",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sources",
                        to="corpus.corpusversion",
                    ),
                ),
            ],
            options={
                "db_table": "source_manifest",
                "ordering": ["source_id"],
            },
        ),
    ]
