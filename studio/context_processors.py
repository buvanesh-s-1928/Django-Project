"""Template context: brand constants shared across the workstation."""
from django.conf import settings


def aura_context(request):
    return {
        "AURA_CURRENCY": settings.CURRENCY_SYMBOL,
        "AURA_ENGINE_MODEL": settings.GEMINI_MODEL,
        "AURA_HAS_SERVER_KEY": bool(settings.GEMINI_API_KEY),
    }
