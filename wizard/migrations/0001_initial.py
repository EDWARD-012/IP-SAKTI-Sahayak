import uuid

import wizard.models

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="WizardSession",
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
                    "session_key",
                    models.CharField(db_index=True, max_length=64, unique=True),
                ),
                (
                    "idempotency_token",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "current_step",
                    models.IntegerField(default=1),
                ),
                (
                    "answers",
                    models.JSONField(blank=True, default=dict),
                ),
                (
                    "completed",
                    models.BooleanField(default=False),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
                (
                    "expires_at",
                    models.DateTimeField(default=wizard.models._default_expires),
                ),
            ],
            options={
                "verbose_name": "Wizard Session",
                "verbose_name_plural": "Wizard Sessions",
                "db_table": "wizard_session",
                "ordering": ["-updated_at"],
            },
        ),
    ]
