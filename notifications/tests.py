from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch

from .models import NotificationTemplate, Trigger


class NotificationAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="admin",
            email="admin@example.com",
            password="securepass123",
            is_staff=True,
            is_superuser=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        self.trigger = Trigger.objects.create(
            name="Login",
            key="login",
            description="User signs in",
        )

        self.email_template = NotificationTemplate.objects.create(
            trigger=self.trigger,
            channel="email",
            name="Login email",
            subject="Welcome back",
            body="Hello {first_name}, you logged in successfully.",
            is_enabled=True,
        )

        self.whatsapp_template = NotificationTemplate.objects.create(
            trigger=self.trigger,
            channel="whatsapp",
            name="Login WhatsApp",
            body="Welcome back {first_name}!",
            is_enabled=True,
        )

        self.web_push_template = NotificationTemplate.objects.create(
            trigger=self.trigger,
            channel="web_push",
            name="Login push",
            title="Welcome back",
            body="Hey {first_name}, welcome back!",
            is_enabled=False,
        )

    @patch("notifications.services.send_email_message")
    @patch("notifications.services.send_whatsapp_message")
    @patch("notifications.services.send_web_push_message")
    def test_fire_trigger_dispatches_enabled_channels(
        self,
        mock_push,
        mock_whatsapp,
        mock_email,
    ):
        mock_email.return_value = {"status": "sent", "channel": "email"}
        mock_whatsapp.return_value = {"status": "sent", "channel": "whatsapp"}
        mock_push.return_value = {"status": "skipped", "channel": "web_push"}

        response = self.client.post(
            "/api/notifications/fire/",
            {
                "trigger": "login",
                "context": {
                    "first_name": "Alice",
                    "email": "alice@example.com",
                    "phone": "+123456789",
                    "subscription": {
                        "endpoint": "https://example.com/subscription",
                        "keys": {"auth": "auth", "p256dh": "p256dh"},
                    },
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["notifications"]), 2)
        mock_email.assert_called_once()
        mock_whatsapp.assert_called_once()
        mock_push.assert_not_called()

    @patch("notifications.services.send_email_message")
    def test_template_test_endpoint_sends_message(self, mock_email):
        mock_email.return_value = {"status": "sent", "channel": "email"}

        response = self.client.post(
            f"/api/notifications/templates/{self.email_template.pk}/test/",
            {
                "context": {
                    "first_name": "Alice",
                    "email": "alice@example.com",
                }
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "sent")
        mock_email.assert_called_once()
