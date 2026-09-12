from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.utils import timezone

User = get_user_model()

from rest_framework.decorators import (
    api_view,
    permission_classes,
)

from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)

from rest_framework.response import Response

from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile
from .serializers import (
    RegisterSerializer,
    UserSerializer,
)

from notifications.models import Trigger, NotificationTemplate
from notifications.services import dispatch_notification


import logging

logger = logging.getLogger(__name__)


def auto_fire_event(user, trigger_key, extra_context=None):
    try:
        trigger = Trigger.objects.filter(key=trigger_key, is_active=True).first()
        if not trigger:
            return
        
        phone_number = ""
        web_push_sub = {}
        if hasattr(user, "profile"):
            phone_number = user.profile.phone_number
            web_push_sub = user.profile.web_push_subscription or {}

        context = {
            "username": user.username,
            "first_name": user.first_name or user.username,
            "email": user.email,
            "phone": phone_number,
            "phone_number": phone_number,
            "subscription": web_push_sub,
            "web_push_subscription": web_push_sub,
        }

        if extra_context and isinstance(extra_context, dict):
            context.update(extra_context)

        templates = NotificationTemplate.objects.filter(trigger=trigger, is_enabled=True)
        for template in templates:
            try:
                res = dispatch_notification(template, context) or {}
                status_val = res.get("status") if isinstance(res, dict) else "sent"
                provider_val = res.get("provider") if isinstance(res, dict) else "unknown"
                print(f"[EVENT FIRED: {trigger_key.upper()}] Channel: {template.channel} | Status: {status_val} | Provider: {provider_val}")
                logger.info(f"Fired {trigger_key} for channel {template.channel}: {res}")
            except Exception as exc:
                print(f"[EVENT ERROR: {trigger_key.upper()}] Channel: {template.channel} | Error: {exc}")
                logger.warning(f"Failed to send {template.channel} for trigger {trigger_key}: {exc}")
    except Exception as exc:
        logger.error(f"Error in auto_fire_event for {trigger_key}: {exc}")



def get_tokens_for_user(user):

    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):

    serializer = RegisterSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    user = serializer.save()

    tokens = get_tokens_for_user(user)

    return Response(
        {
            "message": "User registered successfully",
            "user": UserSerializer(user).data,
            "tokens": tokens,
        },
        status=status.HTTP_201_CREATED
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):

    username = request.data.get("username")

    password = request.data.get("password")

    if not username or not password:

        return Response(
            {
                "error": "Username and password are required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(
        username=username,
        password=password
    )

    if user is None:

        return Response(
            {
                "error": "Invalid username or password"
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    if hasattr(user, "profile"):
        user.profile.last_activity = timezone.now()
        user.profile.save()

    print(auto_fire_event(user, "login"))

    tokens = get_tokens_for_user(user)

    return Response(
        {
            "message": "Login successful",

            "user": UserSerializer(user).data,

            "tokens": tokens,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile_view(request):

    if hasattr(request.user, "profile"):
        request.user.profile.last_activity = timezone.now()
        request.user.profile.save()

    return Response(
        {
            "user": UserSerializer(
                request.user
            ).data
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):

    refresh_token = request.data.get(
        "refresh"
    )

    if not refresh_token:

        return Response(
            {
                "error": "Refresh token is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:

        token = RefreshToken(refresh_token)

        token.blacklist()

        print(auto_fire_event(request.user, "logout"))

        return Response(
            {
                "message": "Logout successful"
            }
        )

    except Exception:

        return Response(
            {
                "error": "Invalid refresh token"
            },
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_view(request):
    username = request.data.get("username")
    email = request.data.get("email")

    if not username and not email:
        return Response({"error": "Email or Username is required"}, status=status.HTTP_400_BAD_REQUEST)

    user = None
    if email:
        user = User.objects.filter(email=email).first()
    if not user and username:
        user = User.objects.filter(username=username).first()

    if user:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        reset_link = f"{frontend_url}/reset-password?uid={uid}&token={token}"

        extra_context = {
            "uid": uid,
            "token": token,
            "reset_token": token,
            "reset_link": reset_link,
        }
        auto_fire_event(user, "password_reset", extra_context=extra_context)

    return Response({
        "message": "If an account exists, a password reset link has been sent."
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    uid = request.data.get("uid")
    token = request.data.get("token")
    new_password = request.data.get("new_password") or request.data.get("password")

    if not uid or not token or not new_password:
        return Response({"error": "uid, token, and new_password are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({"error": "Invalid password reset link or user ID"}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({"error": "Invalid or expired password reset token"}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    return Response({
        "message": "Your password has been reset successfully. You can now log in with your new password."
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def place_order_view(request):
    user = request.user
    item_name = request.data.get("item_name", "Sample Product")
    amount = request.data.get("amount", "$49.99")

    auto_fire_event(user, "order_placed")

    return Response({
        "message": "Order placed successfully!",
        "order": {
            "item": item_name,
            "amount": amount,
            "user": user.username
        }
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_web_push_subscription_view(request):
    subscription = request.data.get("subscription")
    if not subscription:
        return Response({"error": "Subscription payload is required"}, status=status.HTTP_400_BAD_REQUEST)

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.web_push_subscription = subscription
    profile.save()

    return Response({
        "message": "Web Push subscription saved successfully!",
        "subscription": subscription
    }, status=status.HTTP_200_OK)