from django.core.management.base import BaseCommand
from movies.tmdb.sync import sync_all_movies


class Command(BaseCommand):
    help = "Sync TMDB movies (India-focused + pop culture)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=200,
            help="Maximum number of movies to sync",
        )

    def handle(self, *args, **options):
        limit = options["limit"]

        self.stdout.write(f"🎬 Starting TMDB movie sync (limit={limit})...")
        sync_all_movies(limit=limit)
        self.stdout.write(self.style.SUCCESS("✅ Movie sync completed"))
