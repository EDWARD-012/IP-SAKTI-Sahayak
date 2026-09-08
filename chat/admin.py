from django.contrib import admin

from .models import AnswerAudit


@admin.register(AnswerAudit)
class AnswerAuditAdmin(admin.ModelAdmin):
    # query_hmac is HMAC-SHA256 of the original query — never the raw text.
    list_display = [
        "request_id",
        "outcome",
        "jurisdiction",
        "language_code",
        "latency_ms",
        "demo_mode",
        "created_at",
    ]
    readonly_fields = [
        "request_id",
        "query_hmac",
        "query_hmac_key_id",
        "created_at",
    ]
    list_filter = ["outcome", "jurisdiction", "language_code", "demo_mode", "cancelled"]
    search_fields = ["request_id", "corpus_version"]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        # Audit records are written by the application; manual creation is disallowed.
        return False

    def has_change_permission(self, request, obj=None):
        # Audit records are immutable.
        return False
