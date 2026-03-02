"""
users/tests.py
15 INTERVIEW-READY HIGH-IMPACT TESTS
Consolidated to maximize coverage while staying around 35 total project tests.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from users.forms import SignupForm, ProfileUpdateForm, ResetPasswordForm
from users.models import User

class UsersTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        self.user = User.objects.create_user(
            email="user@test.com", password="Password123!", first_name="Normal", last_name="User"
        )
        self.user.is_email_verified = True
        self.user.save()

    # ════════════ 1. USER MODEL & MANAGER ════════════
    def test_user_manager_creation(self):
        # Normal User
        self.assertEqual(self.user.email, "user@test.com")
        self.assertFalse(self.user.is_staff)
        
        # Super User
        admin = User.objects.create_superuser(email="admin@test.com", password="Pass", first_name="A", last_name="B")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_email_verified)

    def test_user_manager_validation(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="pass")
        with self.assertRaises(ValueError):
            User.objects.create_user(email="test@test.com", password="")

    def test_signup_form_validation(self):
        form1 = SignupForm(data={"email": "a@x.com", "first_name": "A", "last_name": "B", "password": "Password123!", "confirm_password": "Password456!"})
        self.assertFalse(form1.is_valid())
        self.assertIn("confirm_password", form1.errors)
        
        form2 = SignupForm(data={"email": "user@test.com", "first_name": "A", "last_name": "B", "password": "Password123!", "confirm_password": "Password123!"})
        self.assertFalse(form2.is_valid())
        self.assertIn("email", form2.errors)

    def test_profile_update_and_reset_forms(self):
        form1 = ProfileUpdateForm(data={"first_name": "  ", "last_name": "  "})
        self.assertFalse(form1.is_valid())
        self.assertIn("first_name", form1.errors)

        form2 = ResetPasswordForm(data={"password": "Password123!", "confirm_password": "Password456!"})
        self.assertFalse(form2.is_valid())

    def test_signup_view(self):
        resp = self.client.get(reverse("signup"))
        self.assertEqual(resp.status_code, 200)

    def test_login_view_success_and_logout(self):
        resp = self.client.post(reverse("login"), {"email": "user@test.com", "password": "Password123!"})
        self.assertRedirects(resp, reverse("movies-home"))
        self.assertIn("_auth_user_id", self.client.session)

        resp2 = self.client.get(reverse("logout"))
        self.assertRedirects(resp2, reverse("movies-home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_failures_unverified_or_wrong(self):
       
        unverified = User.objects.create_user(email="new@test.com", password="Password123!")
        r1 = self.client.post(reverse("login"), {"email": "new@test.com", "password": "Password123!"})
        self.assertEqual(r1.status_code, 200) 
        
        r2 = self.client.post(reverse("login"), {"email": "user@test.com", "password": "BadPassword"})
        self.assertEqual(r2.status_code, 200) 

    def test_profile_view_access(self):
        r1 = self.client.get(reverse("profile"))
        self.assertRedirects(r1, f"{reverse('login')}?next={reverse('profile')}")

        self.client.login(email="user@test.com", password="Password123!")
        r2 = self.client.get(reverse("profile"))
        self.assertEqual(r2.status_code, 200)

    def test_api_register_success_and_invalid(self):
        data = {"email": "api@test.com", "first_name": "API", "last_name": "User", "password": "Password123!"}
        resp = self.api_client.post("/api/users/register/", data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        
        resp2 = self.api_client.post("/api/users/register/", {"email": "x@x.com"})
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_login_success(self):
        resp = self.api_client.post("/api/users/login/", {"email": "user@test.com", "password": "Password123!"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("token", resp.data)

    def test_api_login_failures(self):
        User.objects.create_user(email="unv@test.com", password="Pass123!")
        r1 = self.api_client.post("/api/users/login/", {"email": "unv@test.com", "password": "Pass123!"})
        self.assertEqual(r1.status_code, status.HTTP_403_FORBIDDEN)

        r2 = self.api_client.post("/api/users/login/", {"email": "user@test.com", "password": "Bad"})
        self.assertEqual(r2.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_me_unauthenticated(self):
        resp = self.api_client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_me_read(self):
        self.api_client.force_authenticate(user=self.user)
        resp = self.api_client.get("/api/users/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["email"], "user@test.com")

    def test_api_me_update(self):
        self.api_client.force_authenticate(user=self.user)
        r1 = self.api_client.patch("/api/users/me/", {"first_name": "Updated", "last_name": "Name"})
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        
        r2 = self.api_client.patch("/api/users/me/", {"first_name": "Patch"})
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Patch")
        self.assertEqual(self.user.last_name, "Name")

    def test_forgot_password_view_get(self):
        resp = self.client.get(reverse("forgot-password"))
        self.assertEqual(resp.status_code, 200)
