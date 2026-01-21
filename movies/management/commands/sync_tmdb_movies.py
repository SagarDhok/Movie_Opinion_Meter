from django.core.management.base import BaseCommand
from movies.tmdb.sync import sync_all_movies


class Command(BaseCommand):
    help = "Sync TMDB movies (India-focused + pop culture)"

    def handle(self, *args, **options):
        self.stdout.write("🎬 Starting TMDB movie sync...")
        sync_all_movies()
        self.stdout.write(self.style.SUCCESS("✅ Movie sync completed"))
