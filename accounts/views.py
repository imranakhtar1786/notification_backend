from django.contrib.auth import authenticate
from django.utils import timezone

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

from .serializers import (
    RegisterSerializer,
    UserSerializer,
)

from notifications.models import Trigger, NotificationTemplate
from notifications.services import dispatch_notification


def auto_fire_event(user, trigger_key):
    try:
        trigger = Trigger.objects.filter(key=trigger_key, is_active=True).first()
        if not trigger:
            return
        
        phone_number = ""
        if hasattr(user, "profile"):
            phone_number = user.profile.phone_number

        context = {
            "username": user.username,
            "first_name": user.first_name or user.username,
            "email": user.email,
            "phone": phone_number,
        }

        templates = NotificationTemplate.objects.filter(trigger=trigger, is_enabled=True)
        for template in templates:
            try:
                dispatch_notification(template, context)
            except Exception:
                pass
    except Exception:
        pass


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

    auto_fire_event(user, "login")

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

        auto_fire_event(request.user, "logout")

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

    user = None
    if username:
        user = User.objects.filter(username=username).first()
    elif email:
        user = User.objects.filter(email=email).first()

    if user:
        auto_fire_event(user, "password_reset")
    else:
        # Fallback fire if user context provided
        try:
            trigger = Trigger.objects.filter(key="password_reset", is_active=True).first()
            if trigger:
                context = {
                    "username": username or "User",
                    "first_name": username or "User",
                    "email": email or "",
                    "phone": "",
                }
                templates = NotificationTemplate.objects.filter(trigger=trigger, is_enabled=True)
                for template in templates:
                    dispatch_notification(template, context)
        except Exception:
            pass

    return Response({
        "message": "If an account exists, a password reset notification has been sent."
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