"""`python manage.py seed_aura [--force]` — populate themes/catalog/showcases."""
from django.core.management.base import BaseCommand

from studio.seeds import seed_aura_db


class Command(BaseCommand):
    help = "Seed AURA STAGE defaults: 5 themes, 16 furniture items, 2 showcase blueprints."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true",
                            help="Re-run even if data already exists.")

    def handle(self, *args, **options):
        report = seed_aura_db(force=options["force"])
        if report.get("skipped"):
            self.stdout.write(self.style.WARNING(
                "AURA DB already seeded — use --force to refresh. Report: " + str(report)))
        else:
            self.stdout.write(self.style.SUCCESS("AURA seed complete → " + str(report)))
