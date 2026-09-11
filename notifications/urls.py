from django.urls import path

from .views import (
    trigger_list_create,
    trigger_detail,
    template_list_create,
    template_detail,
    toggle_template,
    test_template,
    fire_trigger,
)


urlpatterns = [

    # Triggers
    path(
        "triggers/",
        trigger_list_create,
        name="trigger-list-create"
    ),

    path(
        "triggers/<int:pk>/",
        trigger_detail,
        name="trigger-detail"
    ),

    # Templates
    path(
        "templates/",
        template_list_create,
        name="template-list-create"
    ),

    path(
        "templates/<int:pk>/",
        template_detail,
        name="template-detail"
    ),

    # Toggle
    path(
        "templates/<int:pk>/toggle/",
        toggle_template,
        name="toggle-template"
    ),

    # Test
    path(
        "templates/<int:pk>/test/",
        test_template,
        name="test-template"
    ),

    # Fire trigger
    path(
        "fire/",
        fire_trigger,
        name="fire-trigger"
    ),
]