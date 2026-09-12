from django.apps import AppConfig
from django.db.models.signals import post_migrate


def populate_default_templates(sender, **kwargs):
    try:
        from .models import Trigger, NotificationTemplate

        triggers_data = [
            ('Login', 'login', 'User signs in on the website'),
            ('Logout', 'logout', 'User signs out'),
            ('Not logged in 1 day', 'not_logged_in_1_day', 'User has not visited for 24 hours'),
            ('Not logged in 1 week', 'not_logged_in_1_week', 'User has not visited for 7 days'),
            ('Password reset', 'password_reset', 'User asks to reset password'),
            ('Order placed', 'order_placed', 'User completes a purchase'),
        ]

        for name, key, desc in triggers_data:
            trig, _ = Trigger.objects.get_or_create(key=key, defaults={'name': name, 'description': desc})

        default_templates = {
            'login': [
                ('whatsapp', 'Login WhatsApp', '', '', 'Welcome back {first_name}! You have successfully signed in to your account.'),
                ('email', 'Login Email', 'Security Alert: New Login', 'New Login Detected', 'Hello {first_name},\n\nWe detected a new login to your account. If this was you, no action is needed.'),
                ('web_push', 'Login Push', '', 'Welcome Back!', 'Hey {first_name}, welcome back to the app!'),
            ],
            'logout': [
                ('whatsapp', 'Logout WhatsApp', '', '', 'Goodbye {first_name}, you have logged out safely. See you soon!'),
                ('email', 'Logout Email', 'You have logged out', 'Logged Out', 'Hi {first_name},\n\nYou have successfully signed out of your session.'),
                ('web_push', 'Logout Push', '', 'Logged Out', 'You have signed out safely.'),
            ],
            'not_logged_in_1_day': [
                ('whatsapp', 'Inactive 1 Day WhatsApp', '', '', 'Hi {first_name}, we noticed you haven\'t visited us today. Check out what\'s new!'),
                ('email', 'Inactive 1 Day Email', 'We miss you!', 'Daily Catch-Up', 'Hello {first_name},\n\nIt\'s been 24 hours since your last visit. Drop by and see what\'s new.'),
                ('web_push', 'Inactive 1 Day Push', '', 'We Miss You!', 'Check out today\'s updates on the platform.'),
            ],
            'not_logged_in_1_week': [
                ('whatsapp', 'Inactive 1 Week WhatsApp', '', '', 'Hello {first_name}, it\'s been a week! We miss you, come back and check your notifications.'),
                ('email', 'Inactive 1 Week Email', 'It\'s been a week...', 'Weekly Update', 'Hi {first_name},\n\nWe haven\'t seen you in 7 days! Log in to catch up on important notifications.'),
                ('web_push', 'Inactive 1 Week Push', '', 'Come Visit Us!', 'It\'s been a week since your last session.'),
            ],
            'password_reset': [
                ('whatsapp', 'Password Reset WhatsApp', '', '', 'Hi {first_name}, use this code to reset your password: 123456.'),
                ('email', 'Password Reset Email', 'Reset Your Password', 'Password Reset Request', 'Hello {first_name},\n\nClick the link below to reset your password.'),
                ('web_push', 'Password Reset Push', '', 'Password Reset Request', 'A password reset request was initiated for your account.'),
            ],
            'order_placed': [
                ('whatsapp', 'Order Placed WhatsApp', '', '', 'Thank you {first_name}! Your order has been placed successfully.'),
                ('email', 'Order Placed Email', 'Order Confirmation', 'Order Placed', 'Hi {first_name},\n\nYour order has been received and is being processed.'),
                ('web_push', 'Order Placed Push', '', 'Order Confirmed', 'Your order was placed successfully!'),
            ]
        }


        for key, tmpls in default_templates.items():
            trig = Trigger.objects.filter(key=key).first()
            if trig:
                for channel, tmpl_name, subject, title, body in tmpls:
                    NotificationTemplate.objects.get_or_create(
                        trigger=trig,
                        channel=channel,
                        defaults={
                            'name': tmpl_name,
                            'subject': subject,
                            'title': title,
                            'body': body,
                            'is_enabled': True,
                        }
                    )
    except Exception:
        pass


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        post_migrate.connect(populate_default_templates, sender=self)

