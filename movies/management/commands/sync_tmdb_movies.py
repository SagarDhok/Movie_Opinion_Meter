from django.core.management.base import BaseCommand
from movies.tmdb.sync import sync_popular_movies
# What is BaseCommand?
# BaseCommand is Django’s base class for CLI commands.
# Every Django command (runserver, migrate, createsuperuser) is built on this.

# Why the class name MUST be Command
# This is not optional.
# Django literally searches for:
# class Command(BaseCommand)

class Command(BaseCommand):
    help = "Sync movies from TMDB"  #"--help shows Django’s global options + my command’s description + any arguments I define."

    def handle(self, *args, **options):
        self.stdout.write("Starting TMDB sync...")
        sync_popular_movies()
        self.stdout.write(self.style.SUCCESS("TMDB sync completed"))


# ✅ sync_tmdb_movies.py

# 👉 CLI command entry point

# ✅ client.py

# 👉 Makes API calls to TMDB using requests

# ✅ sync.py

# 👉 Takes TMDB data → saves into Django DB + sets relationships