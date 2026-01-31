from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from users.models import User
from users.utils import send_brevo_email
from .serializers import ForgotPasswordSerializer,ResetPasswordSerializer
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str



from .serializers import (
    RegisterSerializer,
    UserSerializer,
    UpdateProfileSerializer,
)

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        verify_url = request.build_absolute_uri(
            reverse(
                "verify-email",
                kwargs={"uid": uid, "token": token}
            )
        )

        send_brevo_email(
            to_email=user.email,
            subject="Verify your email – Movie Opinion Meter",
            text_content=f"""
Hi {user.first_name},

Please verify your email to activate your account.

Verification link:
{verify_url}

If you did not sign up, ignore this email.
"""
        )

        return Response(
            {"message": "Registration successful. Please verify your email."},
            status=status.HTTP_201_CREATED
        )



class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(email=email, password=password)

        if not user:
            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_email_verified:
            return Response(
                {"error": "Email not verified"},
                status=status.HTTP_403_FORBIDDEN
            )

        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key
            },
            status=status.HTTP_200_OK
        )
    


class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_url = request.build_absolute_uri(
                reverse(
                    "api-reset-password",
                    kwargs={"uid": uid, "token": token}
                )
            )

            send_brevo_email(
                to_email=user.email,
                subject="Reset your password – Movie Opinion Meter",
                text_content=f"""
                Hi {user.first_name},

                You requested a password reset.

                Reset link:
                {reset_url}

                If you didn’t request this, ignore this email.
                """
                            )


        return Response(
            {"message": "If an account exists, a password reset link has been sent."},
            status=status.HTTP_200_OK
        )



class ResetPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uid, token):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {"error": "Invalid or expired link"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"error": "Invalid or expired link"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"message": "Password reset successful"},
            status=status.HTTP_200_OK
        )




class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UpdateProfileSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Profile updated successfully"})
