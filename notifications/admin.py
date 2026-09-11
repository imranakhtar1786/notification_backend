from django.contrib import admin

from .models import (
    Trigger,
    NotificationTemplate,
)


@admin.register(Trigger)
class TriggerAdmin(admin.ModelAdmin):

    list_display = [
        "name",
        "key",
        "is_active",
        "created_at",
    ]

    search_fields = [
        "name",
        "key",
    ]

    list_filter = [
        "is_active",
    ]


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(
    admin.ModelAdmin
):

    list_display = [
        "name",
        "trigger",
        "channel",
        "is_enabled",
        "created_at",
    ]

    list_filter = [
        "channel",
        "is_enabled",
    ]

    search_fields = [
        "name",
        "body",
    ]