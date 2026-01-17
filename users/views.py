from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes,force_str
from django.urls import reverse
from .utils import send_brevo_email
from django.contrib.auth import authenticate, login






def signup_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        context = {
            "form_data": {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            },
            "errors": {}
        }

        if not email:
            context["errors"]["email"] = "Email is required"

        if not password:
            context["errors"]["password"] = "Password is required"

        if context["errors"]:
            return render(request, "users/signup.html", context)

        if password != confirm_password:
            context["errors"]["confirm_password"] = "Passwords do not match"
            return render(request, "users/signup.html", context)

        if User.objects.filter(email=email).exists():
            context["errors"]["email"] = "Email already registered"
            return render(request, "users/signup.html", context)

        try:
            validate_password(password)
        except ValidationError as e:
            context["errors"]["password"] = e.messages[0]
            return render(request, "users/signup.html", context)
        
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # We encode the user’s data so it can flow properly through the URL without breaking, without causing routing errors, or being misinterpreted.
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        # force_bytes = 12 -> "b12"
        # urlsafe_base64_encode = "b12"->MIT
        token = default_token_generator.make_token(user) #Django automatically sets the token expiry to 24 hours by default.


        verify_url = request.build_absolute_uri( reverse("verify-email", kwargs={"uid": uid,"token": token}))
        #reverse
        #   verify-email/<uidb64>/<token>/"
        # ↓
        # "verify-email/MTI=/c4a-9b7e1f3c2d8a/"


        # build_absolute_uri
        # It converts a relative path into a full, clickable URL.
        # /verify-email/MTI=/abc-token/
        # http://127.0.0.1:8000/verify-email/MTI=/c4a-9b7e1f3c2d8a/



        send_brevo_email(
            to_email=user.email,
            subject="Verify your email – Movie Opinion Meter",
            text_content=f"""
        Hi {user.first_name},

        Please verify your email address to activate your Movie Opinion Meter account.

        Verification link:
        {verify_url}

        This link expires in 24 hours.
        If you did not sign up, you can safely ignore this email.

        – Movie Opinion Meter Team
        """
        )


        return redirect('verify-email-success')
    return render(request, "users/signup.html")




def verify_email(request, uid, token):
    try:
        uid = force_str(urlsafe_base64_decode(uid))
# 1️⃣ urlsafe_base64_decode(uid)
# Input: encoded UID from URL
# "MTI="
# Output: bytes
# b"12"

# force_str(...)
# Input: bytes
# b"12"
# Output: string
# "12"
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        user = None

    if user and default_token_generator.check_token(user, token):# this function checks whether the token really belongs to this user and is still valid (not expired, not tampered).
        user.is_email_verified = True
        user.save()
        messages.success(request, "Email verified successfully. You can now login.")
    else:
        messages.error(request, "Verification link is invalid or expired.")

    return redirect("login")


def verify_email_success(request):
    return render(request, "users/verify_email_success.html")

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        context = {
            "form_data": {
                "email": email,
            },
            "errors": {}
        }

        if not email:
            context["errors"]["email"] = "Email is required"

        if not password:
            context["errors"]["password"] = "Password is required"

        if context["errors"]:
            return render(request, "users/login.html", context)

        user = authenticate(request, email=email, password=password)

        if user is None:
            # generic error (no user enumeration)
            context["errors"]["password"] = "Invalid email or password"
            return render(request, "users/login.html", context)

        if not user.is_email_verified:
            context["errors"]["email"] = "Please verify your email before logging in"
            return render(request, "users/login.html", context)

        login(request, user)
# User → Login Form
#    ↓
# authenticate()
#    ↓
# login(request, user)
#    ↓
# Session created (server)
#    ↓
# sessionid cookie (browser)
#    ↓
# Next requests → request.user available login karych kam nahi ( time limit pan lau shakto) or untill logout
        return redirect("home")

    return render(request, "users/login.html")


def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if not email:
            return render(request,"users/forgot_password.html", {"error": "Email is required"},)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_url = request.build_absolute_uri(
                reverse("reset-password", kwargs={"uid": uid, "token": token})
            )

            send_brevo_email(
                to_email=user.email,
                subject="Reset your password – Movie Opinion Meter",
                text_content=f"""
                Hi {user.first_name},

                You requested a password reset.

                Reset link:
                {reset_url}

                This link expires in 24 hours.
                If you didn’t request this, ignore this email.

                – Movie Opinion Meter Team
                """
                            )

        messages.success(
            request,
            "If an account exists with this email, a password reset link has been sent."
        )
        return redirect("login")

    return render(request, "users/forgot_password.html")


def reset_password_view(request, uid, token):
    try:
        uid = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        user = None

    if not user or not default_token_generator.check_token(user, token):
        messages.error(request, "Reset link is invalid or expired.")
        return redirect("login")

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        errors = {}

        if not password:
            errors["password"] = "Password is required"

        if password != confirm_password:
            errors["confirm_password"] = "Passwords do not match"

        if not errors:
            try:
                validate_password(password, user)
            except ValidationError as e:
                errors["password"] = e.messages[0]

        if errors:
            return render(
                request,
                "users/reset_password.html",
                {"errors": errors},
            )

        user.set_password(password)
        user.save()

        messages.success(request, "Password reset successful. You can now login.")
        return redirect("login")

    return render(request, "users/reset_password.html")
