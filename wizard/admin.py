from django.contrib import admin

from .models import WizardSession


@admin.register(WizardSession)
class WizardSessionAdmin(admin.ModelAdmin):
    list_display = ["session_key", "current_step", "completed", "created_at", "expires_at"]
    list_filter = ["completed"]
    readonly_fields = ["created_at", "updated_at", "idempotency_token"]
    search_fields = ["session_key"]
