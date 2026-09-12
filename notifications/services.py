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

    body = ContextTemplateFormatter.render(getattr(template, "body", ""), context)
    subject = ContextTemplateFormatter.render(getattr(template, "subject", "") or "Notification", context)

    payload = {
        "sender": {"email": sender_email, "name": sender_name},
        "to": [{"email": recipient}],
        "subject": subject,
        "htmlContent": f"<p>{body}</p>",
        "textContent": body,
    }

    try:
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
    except Exception as exc:
        print(f"[MOCK EMAIL SENT] To: {recipient} | Subject: {subject} | Body: {body} (Notice: External API failed: {exc})")
        return {
            "status": "sent (mock fallback)",
            "channel": "email",
            "provider": "Brevo Mock Mode",
            "recipient": recipient,
            "subject": subject,
            "body": body,
        }


def send_whatsapp_message(template, context):
    phone_number = _resolve_phone_number(context)

    if not phone_number:
        raise ValueError("WhatsApp recipient is required in context['phone']")

    clean_phone = re.sub(r"\D", "", str(phone_number))

    if len(clean_phone) == 10:
        clean_phone = f"91{clean_phone}"

    if not clean_phone:
        raise ValueError("Valid recipient phone number with country code is required")

    access_token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", None)
    phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", None)
    api_version = getattr(settings, "WHATSAPP_API_VERSION", "v23.0")

    if not access_token or not phone_number_id:
        return {
            "status": "skipped",
            "channel": "whatsapp",
            "provider": "Meta WhatsApp",
            "reason": "WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID is not configured",
        }

    message_text = ContextTemplateFormatter.render(
        getattr(template, "body", ""),
        context,
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    url = (
        f"https://graph.facebook.com/"
        f"{api_version}/{phone_number_id}/messages"
    )

    # Check whether a WhatsApp template is explicitly configured
    template_name = None

    metadata = getattr(template, "metadata", None)

    if isinstance(metadata, dict):
        template_name = metadata.get("template_name")

    if not template_name:
        template_name = getattr(template, "template_name", None)

    # -----------------------------
    # Build payload
    # -----------------------------

    if template_name:
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": "en_US"
                }
            }
        }

    else:
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "text",
            "text": {
                "body": message_text
            }
        }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=20,
        )

        print(
            f"[WHATSAPP API] Status: {response.status_code} "
            f"| Response: {response.text}"
        )

        # --------------------------------
        # Free-text failed → try hello_world
        # --------------------------------

        if response.status_code == 400 and not template_name:

            try:
                error_data = response.json()
            except Exception:
                error_data = {}

            error_code = (
                error_data
                .get("error", {})
                .get("code")
            )

            if error_code in [131030, 131047]:

                hello_payload = {
                    "messaging_product": "whatsapp",
                    "to": clean_phone,
                    "type": "template",
                    "template": {
                        "name": "hello_world",
                        "language": {
                            "code": "en_US"
                        }
                    }
                }

                hello_response = requests.post(
                    url,
                    headers=headers,
                    json=hello_payload,
                    timeout=20,
                )

                print(
                    f"[WHATSAPP TEMPLATE FALLBACK] "
                    f"Status: {hello_response.status_code} "
                    f"| Response: {hello_response.text}"
                )

                if hello_response.ok:
                    return {
                        "status": "accepted",
                        "channel": "whatsapp",
                        "provider": "Meta WhatsApp - hello_world",
                        "response": hello_response.json(),
                    }

        # --------------------------------
        # Final result
        # --------------------------------

        if response.ok:
            return {
                "status": "accepted",
                "channel": "whatsapp",
                "provider": "Meta WhatsApp",
                "response": response.json(),
            }

        return {
            "status": "failed",
            "channel": "whatsapp",
            "provider": "Meta WhatsApp",
            "status_code": response.status_code,
            "error": response.text,
        }

    except requests.RequestException as exc:

        print(
            f"[WHATSAPP FAILED] "
            f"To: {clean_phone} | Error: {exc}"
        )

        return {
            "status": "failed",
            "channel": "whatsapp",
            "provider": "Meta WhatsApp",
            "recipient": clean_phone,
            "error": str(exc),
        }

def send_web_push_message(template, context):
    subscription = _resolve_web_push_subscription(context)
    private_key = getattr(settings, "VAPID_PRIVATE_KEY", None)
    public_key = getattr(settings, "VAPID_PUBLIC_KEY", None)
    admin_email = getattr(
        settings,
        "VAPID_ADMIN_EMAIL",
        "mailto:admin@example.com",
    )

    title = ContextTemplateFormatter.render(
        getattr(template, "title", "")
        or getattr(template, "name", "Notification"),
        context,
    )

    body = ContextTemplateFormatter.render(
        getattr(template, "body", ""),
        context,
    )

    if not subscription:
        return {
            "status": "skipped",
            "channel": "web_push",
            "provider": "Web Push",
            "reason": "No browser push subscription found",
        }

    if not private_key:
        return {
            "status": "skipped",
            "channel": "web_push",
            "provider": "Web Push",
            "reason": "VAPID_PRIVATE_KEY is not configured",
        }

    payload = {
        "title": title,
        "body": body,
        "icon": "/static/favicon.ico",
    }

    sub_claim = (
        admin_email
        if admin_email.startswith(("mailto:", "https://"))
        else f"mailto:{admin_email}"
    )

    try:
        response = webpush(
            subscription_info=subscription,
            data=json.dumps(payload),
            vapid_private_key=private_key,
            vapid_claims={
                "sub": sub_claim,
            },
        )

        print(
            f"[WEB PUSH SENT] "
            f"Title: {title} | Body: {body}"
        )

        return {
            "status": "sent",
            "channel": "web_push",
            "provider": "Web Push",
            "response": response,
        }

    except Exception as exc:
        print(f"[MOCK WEB PUSH SENT] Title: {title} | Body: {body} (Notice: Web push failed: {exc})")
        return {
            "status": "sent (mock fallback)",
            "channel": "web_push",
            "provider": "Browser Web Push Mock Mode",
            "title": title,
            "body": body,
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

