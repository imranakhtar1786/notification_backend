from django.contrib.auth import authenticate

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