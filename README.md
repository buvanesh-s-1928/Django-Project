# AURA STAGE // LUMINA STUDIO
AI Event Planner & Spatial Furniture Budget Planner — Django 6.1.2, SQLite, zero-install engine.

## Run
    python -m venv .venv && source .venv/bin/activate   # optional
    pip install Django==6.1.2                            # the ONLY dependency
    python manage.py makemigrations studio
    python manage.py migrate                             # auto-seeds themes/catalog/showcases
    python manage.py runserver

Open http://127.0.0.1:8000/  ·  Admin at /admin/ (create one via `manage.py createsuperuser`).

## How it works
- Upload a room photo → POST /api/generate-plan/ → Gemini Vision audit (optional key via the
  telemetry-bar modal) + local Knapsack Budget Optimizer pins real SKUs onto the photo.
- Zero budget overrun is enforced in solver, API and DB (recalc_spent invariant).
- No key? The offline heuristic + knapsack runs 100% locally.
- Re-seed anytime: `python manage.py seed_aura --force`.
