from django.core.management.base import BaseCommand
from movies.tmdb.sync_cast import sync_cast_and_crew


class Command(BaseCommand):
    help = "Sync TMDB cast, crew and person biography"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)

    def handle(self, *args, **options):
        self.stdout.write("🎭 Syncing cast & crew...")
        sync_cast_and_crew(limit=options["limit"])
        self.stdout.write(self.style.SUCCESS("✅ Cast & crew sync complete"))
