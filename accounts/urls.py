from django.urls import path

from .views import (
    register_view,
    login_view,
    logout_view,
    profile_view,
    password_reset_view,
    password_reset_confirm_view,
    place_order_view,
    save_web_push_subscription_view,
)


urlpatterns = [

    path(
        "register/",
        register_view,
        name="register"
    ),

    path(
        "login/",
        login_view,
        name="login"
    ),

    path(
        "logout/",
        logout_view,
        name="logout"
    ),

    path(
        "profile/",
        profile_view,
        name="profile"
    ),

    path(
        "password-reset/",
        password_reset_view,
        name="password-reset"
    ),

    path(
        "password-reset-confirm/",
        password_reset_confirm_view,
        name="password-reset-confirm"
    ),

    path(
        "place-order/",
        place_order_view,
        name="place-order"
    ),

    path(
        "web-push-subscription/",
        save_web_push_subscription_view,
        name="web-push-subscription"
    ),
]