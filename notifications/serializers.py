from rest_framework import serializers

from .models import (
    Trigger,
    NotificationTemplate,
)


class NotificationTemplateSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = NotificationTemplate

        fields = [
            "id",
            "trigger",
            "channel",
            "name",
            "subject",
            "title",
            "body",
            "is_enabled",
            "variable_mapping",
            "created_by",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "created_by",
            "created_at",
            "updated_at",
        ]


class TriggerSerializer(
    serializers.ModelSerializer
):

    templates = NotificationTemplateSerializer(
        many=True,
        read_only=True
    )

    class Meta:

        model = Trigger

        fields = [
            "id",
            "name",
            "key",
            "description",
            "is_active",
            "templates",
            "created_at",
            "updated_at",
        ]