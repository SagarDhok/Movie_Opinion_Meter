from django.core.management.base import BaseCommand
from movies.tmdb.sync import sync_all_movies


class Command(BaseCommand):
    help = "Sync TMDB movies (India-focused + pop culture only)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting TMDB sync...\n"))
        sync_all_movies()
        self.stdout.write(self.style.SUCCESS("\n🎉 TMDB sync completed"))
