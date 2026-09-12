from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

    list_display = [
        "username",
        "email",
        "get_phone_number",
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
        "profile__phone_number",
    ]

    def get_phone_number(self, obj):
        if hasattr(obj, "profile"):
            return obj.profile.phone_number
        return ""

    get_phone_number.short_description = "Phone Number"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "phone_number", "last_activity"]
    search_fields = ["user__username", "user__email", "phone_number"]