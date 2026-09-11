import json
import re
from collections.abc import Mapping

import requests
from django.conf import settings
from pywebpush import webpush


class ContextTemplateFormatter:
    @staticmethod
    def _flatten_context(value, parent_key="", result=None):
        if result is None:
            result = {}

        if isinstance(value, Mapping):
            for key, item in value.items():
                nested_key = f"{parent_key}.{key}" if parent_key else str(key)
                ContextTemplateFormatter._flatten_context(item, nested_key, result)
        else:
            if parent_key:
                result[parent_key] = value

        return result

    @classmethod
    def render(cls, template_text, context):
        if template_text is None:
            return ""

        flattened = cls._flatten_context(context)
        normalized = {key: value for key, value in flattened.items()}

        for key, value in context.items():
            if key not in normalized:
                normalized[key] = value

        def replace_missing(match):
            key = match.group(1).strip()
            return str(normalized.get(key, ""))

        rendered = re.sub(r"\{\s*([A-Za-z0-9_\.]+)\s*\}", replace_missing, str(template_text))
        return rendered


def _resolve_email_recipient(context):
    return (
        context.get("email")
        or context.get("recipient_email")
        or context.get("user_email")
    )


def _resolve_phone_number(context):
    return (
        context.get("phone")
        or context.get("whatsapp")
        or context.get("phone_number")
        or context.get("recipient_phone")
    )


def _resolve_web_push_subscription(context):
    return (
        context.get("subscription")
        or context.get("web_push_subscription")
        or context.get("push_subscription")
    )


def send_email_message(template, context):
    recipient = _resolve_email_recipient(context)
    if not recipient:
        raise ValueError("Email recipient is required in context['email']")

    api_key = getattr(settings, "BREVO_API_KEY", None)
    sender_email = getattr(settings, "BREVO_FROM_EMAIL", None)
    sender_name = getattr(settings, "BREVO_FROM_NAME", "Notification System")

    if not api_key or not sender_email:
        return {
            "status": "skipped",
            "channel": "email",
            "reason": "BREVO_API_KEY or BREVO_FROM_EMAIL is not configured",
        }

    payload = {
        "sender": {"email": sender_email, "name": sender_name},
        "to": [{"email": recipient}],
        "subject": ContextTemplateFormatter.render(getattr(template, "subject", "") or "Notification", context),
        "htmlContent": f"<p>{ContextTemplateFormatter.render(getattr(template, 'body', ''), context)}</p>",
        "textContent": ContextTemplateFormatter.render(getattr(template, "body", ""), context),
    }

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=payload,
        timeout=20,
    )
    response.raise_for_status()
    return {
        "status": "sent",
        "channel": "email",
        "provider": "Brevo",
        "response": response.json(),
    }


def send_whatsapp_message(template, context):
    phone_number = _resolve_phone_number(context)
    if not phone_number:
        raise ValueError("WhatsApp recipient is required in context['phone']")

    access_token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", None)
    phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", None)
    api_version = getattr(settings, "WHATSAPP_API_VERSION", "v23.0")

    if not access_token or not phone_number_id:
        return {
            "status": "skipped",
            "channel": "whatsapp",
            "reason": "WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID is not configured",
        }

    message_text = ContextTemplateFormatter.render(getattr(template, "body", ""), context)
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message_text},
    }
    response = requests.post(
        f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )
    response.raise_for_status()
    return {
        "status": "sent",
        "channel": "whatsapp",
        "provider": "Meta WhatsApp",
        "response": response.json(),
    }


def send_web_push_message(template, context):
    subscription = _resolve_web_push_subscription(context)
    if not subscription:
        raise ValueError("Web push subscription is required in context['subscription']")

    private_key = getattr(settings, "VAPID_PRIVATE_KEY", None)
    public_key = getattr(settings, "VAPID_PUBLIC_KEY", None)
    admin_email = getattr(settings, "VAPID_ADMIN_EMAIL", "mailto:admin@example.com")

    if not private_key or not public_key:
        return {
            "status": "skipped",
            "channel": "web_push",
            "reason": "VAPID_PRIVATE_KEY or VAPID_PUBLIC_KEY is not configured",
        }

    payload = {
        "title": ContextTemplateFormatter.render(getattr(template, "title", "") or getattr(template, "name", "Notification"), context),
        "body": ContextTemplateFormatter.render(getattr(template, "body", ""), context),
        "icon": "/static/favicon.ico",
    }

    webpush(
        subscription_info=subscription,
        data=json.dumps(payload),
        vapid_private_key=private_key,
        vapid_claims={"sub": admin_email},
        vapid_pem=None,
    )

    return {
        "status": "sent",
        "channel": "web_push",
        "provider": "Web Push",
    }


def dispatch_notification(template, context):
    if template.channel == "email":
        return send_email_message(template, context)
    if template.channel == "whatsapp":
        return send_whatsapp_message(template, context)
    if template.channel == "web_push":
        return send_web_push_message(template, context)

    return {
        "status": "skipped",
        "channel": template.channel,
        "reason": "Unsupported channel",
    }
