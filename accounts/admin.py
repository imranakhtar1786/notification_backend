from django.contrib import admin
from django.contrib.auth.models import User


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):

    list_display = [
        "username",
        "email",
        "is_staff",
        "is_superuser",
        "is_active",
    ]

    list_filter = [
        "is_staff",
        "is_superuser",
        "is_active",
    ]

    search_fields = [
        "username",
        "email",
    ]