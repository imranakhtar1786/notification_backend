from django.contrib import admin

from django.urls import (
    path,
    include,
)

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)


urlpatterns = [

    path(
        "django-admin/",
        admin.site.urls
    ),

    path(
        "api/auth/",
        include("accounts.urls")
    ),

    path(
        "api/notifications/",
        include("notifications.urls")
    ),

    path(
        "api/auth/token/refresh/",
        TokenRefreshView.as_view()
    ),
]