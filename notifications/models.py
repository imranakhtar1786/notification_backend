from django.db import models
from django.contrib.auth.models import User


class Trigger(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    key = models.SlugField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class NotificationTemplate(models.Model):

    CHANNEL_CHOICES = [
        ("whatsapp", "WhatsApp"),
        ("email", "Email"),
        ("web_push", "Web Push"),
    ]

    trigger = models.ForeignKey(
        Trigger,
        on_delete=models.CASCADE,
        related_name="templates"
    )

    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES
    )

    name = models.CharField(
        max_length=150
    )

    subject = models.CharField(
        max_length=255,
        blank=True
    )

    title = models.CharField(
        max_length=255,
        blank=True
    )

    body = models.TextField()

    is_enabled = models.BooleanField(
        default=True
    )

    variable_mapping = models.JSONField(
        default=dict,
        blank=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["trigger", "channel"],
                name="unique_trigger_channel"
            )
        ]

    def __str__(self):
        return f"{self.trigger.name} - {self.channel}"