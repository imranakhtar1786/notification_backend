from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default=""
    )
    last_activity = models.DateTimeField(
        default=timezone.now
    )
    web_push_subscription = models.JSONField(
        default=dict,
        blank=True
    )


    def __str__(self):
        return f"{self.user.username}'s profile"

