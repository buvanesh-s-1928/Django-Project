from django.apps import AppConfig


class StudioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "studio"
    verbose_name = "Lumina Studio — AURA Stage"

    def ready(self):
        # Auto-seed the AURA database on first launch (safe, idempotent).
        from studio.seeds import ensure_aura_seed

        ensure_aura_seed()
