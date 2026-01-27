from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = "Create superuser from env vars if not exists"

    def handle(self, *args, **options):
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not email or not password:
            self.stdout.write("❌ Superuser env vars missing")
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write("ℹ️ Superuser already exists")
            return

        User.objects.create_superuser(
            email=email,
            password=password
        )

        self.stdout.write("✅ Superuser created")
