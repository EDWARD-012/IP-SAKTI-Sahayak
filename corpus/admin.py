from django.contrib import admin

from .models import CorpusVersion, SourceManifest


@admin.action(description="Activate selected corpus version")
def activate_version(modeladmin, request, queryset):
    if queryset.count() != 1:
        modeladmin.message_user(
            request,
            "Select exactly one corpus version to activate.",
            level="error",
        )
        return
    cv = queryset.first()
    cv.activate()
    modeladmin.message_user(
        request,
        f"Corpus version \u2018{cv.version}\u2019 is now active.",
        level="success",
    )


@admin.register(CorpusVersion)
class CorpusVersionAdmin(admin.ModelAdmin):
    list_display = ["version", "status", "chunks_count", "created_at"]
    list_filter = ["status"]
    readonly_fields = ["created_at", "activated_at", "retired_at"]
    search_fields = ["version", "chroma_collection"]
    actions = [activate_version]


@admin.register(SourceManifest)
class SourceManifestAdmin(admin.ModelAdmin):
    list_display = ["source_id", "title", "authority", "ip_types", "effective_status"]
    list_filter = ["effective_status", "reuse_basis", "jurisdiction"]
    search_fields = ["source_id", "title", "authority"]
    readonly_fields = ["source_id"]
