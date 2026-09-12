from django.urls import path

from .views import (
    register_view,
    login_view,
    logout_view,
    profile_view,
    password_reset_view,
    place_order_view,
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
        "place-order/",
        place_order_view,
        name="place-order"
    ),
]