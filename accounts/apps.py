from django.apps import AppConfig
from django.db.models.signals import post_save


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        from .models import UserProfile
        UserProfile.objects.get_or_create(user=instance)


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        post_save.connect(create_user_profile, sender=User)

