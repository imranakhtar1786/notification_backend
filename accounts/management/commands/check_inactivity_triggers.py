from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import UserProfile
from notifications.models import Trigger, NotificationTemplate
from notifications.services import dispatch_notification


class Command(BaseCommand):
    help = "Checks user inactivity and fires inactive triggers (1 day / 1 week)"

    def handle(self, *args, **options):
        now = timezone.now()
        one_day_ago = now - timedelta(days=1)
        one_week_ago = now - timedelta(days=7)

        trig_1day = Trigger.objects.filter(key="not_logged_in_1_day", is_active=True).first()
        trig_1week = Trigger.objects.filter(key="not_logged_in_1_week", is_active=True).first()

        profiles = UserProfile.objects.all()

        count_1day = 0
        count_1week = 0

        for profile in profiles:
            user = profile.user
            phone = profile.phone_number
            context = {
                "username": user.username,
                "first_name": user.first_name or user.username,
                "email": user.email,
                "phone": phone,
            }

            if trig_1week and profile.last_activity <= one_week_ago:
                templates = NotificationTemplate.objects.filter(trigger=trig_1week, is_enabled=True)
                for template in templates:
                    try:
                        dispatch_notification(template, context)
                        count_1week += 1
                    except Exception:
                        pass
            elif trig_1day and profile.last_activity <= one_day_ago:
                templates = NotificationTemplate.objects.filter(trigger=trig_1day, is_enabled=True)
                for template in templates:
                    try:
                        dispatch_notification(template, context)
                        count_1day += 1
                    except Exception:
                        pass

        self.stdout.write(self.style.SUCCESS(f"Dispatched {count_1day} 1-day inactivity and {count_1week} 1-week inactivity notifications."))
