from django.shortcuts import get_object_or_404

from rest_framework.decorators import (
    api_view,
    permission_classes,
)

from rest_framework.permissions import (
    IsAuthenticated,
)

from rest_framework.response import Response

from rest_framework import status

from .models import (
    Trigger,
    NotificationTemplate,
)

from .serializers import (
    TriggerSerializer,
    NotificationTemplateSerializer,
)

from .permissions import IsAdminUser
from .services import dispatch_notification


# ==================================================
# TRIGGERS
# ==================================================


@api_view(["GET", "POST"])
@permission_classes([
    IsAuthenticated,
    IsAdminUser,
])
def trigger_list_create(request):

    if request.method == "GET":

        triggers = Trigger.objects.all()

        serializer = TriggerSerializer(
            triggers,
            many=True
        )

        return Response(
            serializer.data
        )

    serializer = TriggerSerializer(
        data=request.data
    )

    if not serializer.is_valid():

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    trigger = serializer.save()

    return Response(
        TriggerSerializer(trigger).data,
        status=status.HTTP_201_CREATED
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([
    IsAuthenticated,
    IsAdminUser,
])
def trigger_detail(request, pk):

    trigger = get_object_or_404(
        Trigger,
        pk=pk
    )

    if request.method == "GET":

        serializer = TriggerSerializer(
            trigger
        )

        return Response(
            serializer.data
        )

    if request.method in ["PUT", "PATCH"]:

        serializer = TriggerSerializer(
            trigger,
            data=request.data,
            partial=request.method == "PATCH"
        )

        if not serializer.is_valid():

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        return Response(
            serializer.data
        )

    trigger.delete()

    return Response(
        {
            "message": "Trigger deleted successfully"
        }
    )


# ==================================================
# TEMPLATES
# ==================================================


@api_view(["GET", "POST"])
@permission_classes([
    IsAuthenticated,
    IsAdminUser,
])
def template_list_create(request):

    if request.method == "GET":

        templates = NotificationTemplate.objects.all()

        serializer = NotificationTemplateSerializer(
            templates,
            many=True
        )

        return Response(
            serializer.data
        )

    serializer = NotificationTemplateSerializer(
        data=request.data
    )

    if not serializer.is_valid():

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    template = serializer.save(
        created_by=request.user
    )

    return Response(
        NotificationTemplateSerializer(
            template
        ).data,
        status=status.HTTP_201_CREATED
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([
    IsAuthenticated,
    IsAdminUser,
])
def template_detail(request, pk):

    template = get_object_or_404(
        NotificationTemplate,
        pk=pk
    )

    if request.method == "GET":

        serializer = NotificationTemplateSerializer(
            template
        )

        return Response(
            serializer.data
        )

    if request.method in ["PUT", "PATCH"]:

        serializer = NotificationTemplateSerializer(
            template,
            data=request.data,
            partial=request.method == "PATCH"
        )

        if not serializer.is_valid():

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        return Response(
            serializer.data
        )

    template.delete()

    return Response(
        {
            "message": "Template deleted successfully"
        }
    )


# ==================================================
# TOGGLE CHANNEL
# ==================================================


@api_view(["PATCH"])
@permission_classes([
    IsAuthenticated,
    IsAdminUser,
])
def toggle_template(request, pk):

    template = get_object_or_404(
        NotificationTemplate,
        pk=pk
    )

    template.is_enabled = not template.is_enabled

    template.save()

    return Response(
        {
            "message": "Template status updated",

            "id": template.id,

            "channel": template.channel,

            "is_enabled": template.is_enabled,
        }
    )


# ==================================================
# TEST SEND
# ==================================================


@api_view(["POST"])
@permission_classes([
    IsAuthenticated,
    IsAdminUser,
])
def test_template(request, pk):

    template = get_object_or_404(
        NotificationTemplate,
        pk=pk
    )

    context = request.data.get("context", {})

    # Auto-fill recipient context from authenticated admin user if not provided
    if (not context.get("email") or not str(context.get("email")).strip()) and request.user.email:
        context["email"] = request.user.email
    if (not context.get("phone") or not str(context.get("phone")).strip()) and hasattr(request.user, "profile") and request.user.profile.phone_number:
        context["phone"] = request.user.profile.phone_number
        context["phone_number"] = request.user.profile.phone_number

    if not context.get("subscription") and not context.get("web_push_subscription"):
        if hasattr(request.user, "profile") and request.user.profile.web_push_subscription:
            context["subscription"] = request.user.profile.web_push_subscription
            context["web_push_subscription"] = request.user.profile.web_push_subscription

    if not context.get("name") and not context.get("first_name"):
        context["name"] = request.user.first_name or request.user.username
        context["first_name"] = request.user.first_name or request.user.username

    try:
        result = dispatch_notification(template, context)
    except ValueError as exc:
        return Response(
            {
                "error": str(exc),
                "template_id": template.id,
                "channel": template.channel,
                "status": "failed",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "message": "Test notification sent",
            "template_id": template.id,
            "channel": template.channel,
            "status": result.get("status", "success"),
            "provider": result.get("provider"),
            "details": result,
        }
    )


@api_view(["POST"])
@permission_classes([
    IsAuthenticated,
])
def fire_trigger(request):

    trigger_key = request.data.get(
        "trigger"
    )

    context = request.data.get(
        "context",
        {}
    )

    if not trigger_key:

        return Response(
            {
                "error": "trigger is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    trigger = get_object_or_404(
        Trigger,
        key=trigger_key,
        is_active=True
    )

    # Auto-fill context from user if missing
    if (not context.get("email") or not str(context.get("email")).strip()) and request.user.email:
        context["email"] = request.user.email
    if (not context.get("phone") or not str(context.get("phone")).strip()) and hasattr(request.user, "profile") and request.user.profile.phone_number:
        context["phone"] = request.user.profile.phone_number
        context["phone_number"] = request.user.profile.phone_number

    if not context.get("subscription") and not context.get("web_push_subscription"):
        if hasattr(request.user, "profile") and request.user.profile.web_push_subscription:
            context["subscription"] = request.user.profile.web_push_subscription
            context["web_push_subscription"] = request.user.profile.web_push_subscription

    if not context.get("name") and not context.get("first_name"):
        context["name"] = request.user.first_name or request.user.username
        context["first_name"] = request.user.first_name or request.user.username

    templates = NotificationTemplate.objects.filter(
        trigger=trigger,
        is_enabled=True
    )

    results = []

    for template in templates:
        try:
            result = dispatch_notification(template, context)
            status_value = result.get("status", "queued")
        except ValueError as exc:
            status_value = "failed"
            result = {
                "status": "failed",
                "channel": template.channel,
                "reason": str(exc),
            }

        results.append(
            {
                "channel": template.channel,
                "template_id": template.id,
                "status": status_value,
                "context": context,
                "details": result,
            }
        )


    return Response(
        {
            "trigger": trigger.key,
            "message": "Trigger fired successfully",
            "notifications": results,
        }
    )