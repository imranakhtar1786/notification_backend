from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserProfile


class RegisterSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        write_only=True
    )

    password = serializers.CharField(
        write_only=True,
        min_length=6
    )

    class Meta:
        model = User

        fields = [
            "username",
            "email",
            "password",
            "phone_number",
        ]

    def create(self, validated_data):
        phone_number = validated_data.pop("phone_number", "")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )

        profile, _ = UserProfile.objects.get_or_create(user=user)
        if phone_number:
            profile.phone_number = phone_number
            profile.save()

        return user


class UserSerializer(serializers.ModelSerializer):
    phone_number = serializers.SerializerMethodField()

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "is_staff",
            "is_superuser",
        ]

    def get_phone_number(self, obj):
        if hasattr(obj, "profile"):
            return obj.profile.phone_number
        return ""
   