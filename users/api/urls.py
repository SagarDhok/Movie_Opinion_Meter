from django.urls import path
from .views import (
    RegisterAPIView,
    LoginAPIView,
    MeAPIView,
    ForgotPasswordAPIView,
    ResetPasswordAPIView,
)

urlpatterns = [
    path("register/", RegisterAPIView.as_view()),
    path("login/", LoginAPIView.as_view()),
    path("me/", MeAPIView.as_view()),

    path("forgot-password/", ForgotPasswordAPIView.as_view()),
    path("reset-password/<uid>/<token>/",ResetPasswordAPIView.as_view(),name="api-reset-password",
    ),
]
