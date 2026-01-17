from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("verify-email-success/", views.verify_email_success, name="verify-email-success"),
    path("verify-email/<uid>/<token>/",views.verify_email,name="verify-email"),
    
    path("forgot-password/", views.forgot_password_view, name="forgot-password"),
    path("reset-password/<uid>/<token>/", views.reset_password_view, name="reset-password")


]
