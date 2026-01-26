from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("signup/", views.signup_view, name="signup"),

    path("verify-email-success/", views.verify_email_success, name="verify-email-success"),
    path("verify-email/<uid>/<token>/", views.verify_email, name="verify-email"),

    path("profile/", views.profile_view, name="profile"),

    path("forgot-password/", views.forgot_password_view, name="forgot-password"),
    path("reset-password/<uid>/<token>/", views.reset_password_view, name="reset-password"),

    path("<int:user_id>/", views.public_profile, name="public_profile"),
    path("my-reviews/", views.my_reviews, name="my-reviews"),
    
]
