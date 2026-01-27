from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()


class Command(BaseCommand):
    help = "Create superuser from environment variables if it does not exist"

    def handle(self, *args, **options):
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        first_name = os.environ.get("DJANGO_SUPERUSER_FIRST_NAME", "")
        last_name = os.environ.get("DJANGO_SUPERUSER_LAST_NAME", "")

        if not email or not password:
            self.stdout.write(self.style.ERROR("❌ Superuser env vars missing"))
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING("ℹ️ Superuser already exists"))
            return

        User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        self.stdout.write(self.style.SUCCESS("✅ Superuser created successfully"))
