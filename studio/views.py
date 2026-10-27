"""
AURA STAGE // LUMINA STUDIO — Views
Single-page workstation backend:
  GET  /                          → index (the interactive workstation)
  POST /api/generate-plan/        → upload room photo + run AI/Knapsack engine
  GET  /api/blueprints/           → saved vault payload
  GET  /api/blueprint/<id>/       → full staged plan payload for one blueprint
  POST /api/blueprint/<id>/pin/   → persist a dragged pin position (x%, y%)
  POST /api/blueprint/<id>/add-item/ → "+ Add to Room" from the catalog
  POST /api/blueprint/<id>/remove-pin/ → delete a staged item
  POST /api/copilot/              → re-optimise with a natural-language prompt
"""
import json
import logging
import re

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .engine import heuristic_audit, knapsack_optimize, run_generation_pipeline
from .models import EventBlueprint, EventTheme, FurnitureItem, StagedFurniture
from .seeds import seed_aura_db

logger = logging.getLogger("studio")


# ------------------------------------------------------------------ #
#  Helpers                                                            #
# ------------------------------------------------------------------ #
def _json_body(request):
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            return {}
    return {k: v for k, v in request.POST.items()}


def _resolve_api_key(request, body=None):
    """Key precedence: request body > session stash > settings server key."""
    body = body or {}
    key = (body.get("gemini_key") or "").strip()
    if key:
        request.session["aura_gemini_key"] = key
        return key
    return request.session.get("aura_gemini_key", "") or getattr(
        __import__("django.conf", fromlist=["settings"]).settings, "GEMINI_API_KEY", ""
    )


def _f(body, name, default=None):
    raw = body.get(name)
    if raw in (None, ""):
        return default
    try:
        return float(str(raw).replace(",", "").replace("₹", "").strip())
    except (TypeError, ValueError):
        return default


def blueprint_payload(bp, with_pins=True):
    data = {
        "id": bp.pk,
        "title": bp.title,
        "theme": {"code": bp.theme.code, "name": bp.theme.name,
                  "accent": bp.theme.accent_hex, "vibe": bp.theme.vibe},
        "guest_count": bp.guest_count,
        "budget": float(bp.budget_inr),
        "spent": float(bp.spent_inr),
        "headroom": round(float(bp.budget_inr) - float(bp.spent_inr), 2),
        "status": bp.status,
        "engine": bp.ai_engine,
        "ai_summary": bp.ai_summary,
        "run_of_show": bp.run_of_show_list(),
        "photo_url": bp.room_photo.url if bp.room_photo else None,
        "room": {"width_ft": float(bp.room_width_ft),
                 "depth_ft": float(bp.room_depth_ft),
                 "area_sqft": bp.room_area_sqft},
        "created_at": bp.created_at.strftime("%d %b %Y · %H:%M"),
        "is_showcase": bp.is_showcase,
    }
    if with_pins:
        data["pins"] = [{
            "pin_id": s.pk,
            "sku": s.item.sku,
            "name": s.item.name,
            "category": s.item.category,
            "qty": s.quantity,
            "unit_price": float(s.item.price_inr),
            "line_total": float(s.line_total),
            "x": float(s.pin_x_pct),
            "y": float(s.pin_y_pct),
            "note": s.note,
            "placed_by": s.placed_by,
        } for s in bp.staged_set.select_related("item").order_by("pin_y_pct")]
    return data


# ==================================================================== #
#  PAGE                                                               #
# ==================================================================== #
def index(request):
    """The AURA Stage workstation — one page, everything live."""
    themes = EventTheme.objects.all()
    catalog = FurnitureItem.objects.filter(in_stock=True)
    blueprints = EventBlueprint.objects.select_related("theme").prefetch_related(
        "staged_set__item"
    ).all()[:12]

    context = {
        "themes": themes,
        "catalog": catalog,
        "blueprints": blueprints,
        "showcases": [blueprint_payload(bp, with_pins=False) for bp in blueprints
                      if bp.is_showcase],
        "vault": [blueprint_payload(bp, with_pins=False) for bp in blueprints],
        "catalog_json": [
            {
                "id": i.pk, "sku": i.sku, "name": i.name, "category": i.category,
                "price": float(i.price_inr), "footprint": float(i.footprint_sqft),
                "capacity": i.guest_capacity, "aura": i.aesthetic_score,
                "material": i.material, "palette": i.palette_tag,
                "blurb": i.blurb, "themes": i.theme_codes,
            } for i in catalog
        ],
        "themes_json": [
            {
                "code": t.code, "name": t.name, "tagline": t.tagline,
                "vibe": t.vibe, "accent": t.accent_hex,
                "split": {"seating": float(t.seating_ratio),
                          "decor": float(t.decor_ratio),
                          "hospitality": float(t.hospitality_ratio)},
            } for t in themes
        ],
    }
    return render(request, "studio/index.html", context)


# ==================================================================== #
#  POST /api/generate-plan/                                           #
# ==================================================================== #
@csrf_exempt
@require_POST
def generate_plan(request):
    """Accepts multipart form-data:
        title, theme_code, guest_count, budget_inr, room_width_ft,
        room_depth_ft, host_name, event_date, room_photo (file), gemini_key
    Runs the AI Vision + Knapsack pipeline and returns the full plan JSON.
    """
    body = request.POST.dict()
    file_obj = request.FILES.get("room_photo")

    theme_code = (body.get("theme_code") or "").strip()
    theme = get_object_or_404(EventTheme, code=theme_code)

    title = (body.get("title") or f"{theme.name} Stage Plan").strip()[:140]
    guests = int(_f(body, "guest_count", 20) or 20)
    budget = _f(body, "budget_inr", 50000) or 50000
    width = _f(body, "room_width_ft", 14) or 14
    depth = _f(body, "room_depth_ft", 16) or 16

    if budget < 1000:
        return JsonResponse({"ok": False,
                             "error": "Minimum working budget is ₹1,000."}, status=400)

    api_key = _resolve_api_key(request, body)

    try:
        with transaction.atomic():
            bp = EventBlueprint.objects.create(
                title=title, theme=theme,
                host_name=(body.get("host_name") or "").strip()[:120],
                guest_count=max(min(guests, 400), 1),
                budget_inr=budget,
                room_width_ft=width, room_depth_ft=depth,
                status=EventBlueprint.Status.DRAFT,
                ai_engine="pending",
            )
            if file_obj:
                bp.room_photo.save(file_obj.name, file_obj, save=True)
    except ValidationError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    try:
        plan = run_generation_pipeline(bp, api_key=api_key)
    except Exception as exc:  # noqa: BLE001 — engine must never 500 the UX
        logger.exception("AURA engine failure")
        return JsonResponse({
            "ok": False,
            "error": f"Engine fault: {exc}. Retry — the offline knapsack will run.",
            "blueprint_id": bp.pk,
        }, status=500)

    plan["ok"] = True
    plan["title"] = bp.title
    return JsonResponse(plan, safe=False)


# ==================================================================== #
#  Vault & single-blueprint reads                                       #
# ==================================================================== #
@require_GET
def blueprint_list(request):
    bps = (EventBlueprint.objects.select_related("theme")
           .prefetch_related("staged_set__item").all()[:40])
    return JsonResponse({"ok": True, "blueprints": [blueprint_payload(b) for b in bps]})


@require_GET
def blueprint_detail(request, pk: int):
    bp = get_object_or_404(EventBlueprint.objects.select_related("theme")
                          .prefetch_related("staged_set__item"), pk=pk)
    return JsonResponse({"ok": True, **blueprint_payload(bp)})


# ==================================================================== #
#  Pinboard mutations                                                 #
# ==================================================================== #
def _mutate_guard(bp: EventBlueprint):
    """Re-enforce the zero-overrun invariant after any manual change."""
    bp.refresh_from_db()
    spent = sum(float(s.line_total) for s in bp.staged_set.all())
    return spent <= float(bp.budget_inr)


@csrf_exempt
@require_POST
def move_pin(request, pk: int):
    bp = get_object_or_404(EventBlueprint, pk=pk)
    body = _json_body(request)
    pin_id = body.get("pin_id")
    x = _f(body, "x"); y = _f(body, "y")
    if pin_id is None or x is None or y is None:
        return JsonResponse({"ok": False, "error": "pin_id, x, y required"}, status=400)
    stage = get_object_or_404(StagedFurniture, pk=pin_id, blueprint=bp)
    stage.pin_x_pct = min(max(x, 0), 100)
    stage.pin_y_pct = min(max(y, 0), 100)
    stage.placed_by = "manual"
    stage.save(update_fields=["pin_x_pct", "pin_y_pct", "placed_by"])
    bp.recalc_spent(commit=True)
    return JsonResponse({"ok": True, "spent": float(bp.spent_inr),
                         "headroom": bp.budget_headroom,
                         "pin": {"pin_id": stage.pk, "x": float(stage.pin_x_pct),
                                 "y": float(stage.pin_y_pct)}})


@csrf_exempt
@require_POST
def add_item_to_room(request, pk: int):
    bp = get_object_or_404(EventBlueprint, pk=pk)
    body = _json_body(request)
    item = get_object_or_404(FurnitureItem, pk=body.get("item_id"))

    existing = StagedFurniture.objects.filter(blueprint=bp, item=item).first()
    if existing:
        new_qty = existing.quantity + 1
    else:
        new_qty = 1

    projected = float(bp.spent_inr) + float(item.price_inr) * (
        1 if not existing else 1
    )
    if projected > float(bp.budget_inr):
        return JsonResponse({
            "ok": False,
            "error": (f"Adding “{item.name}” would push spend to ₹{projected:,.0f} "
                      f"over the ₹{float(bp.budget_inr):,.0f} ceiling. "
                      f"AURA blocks overruns by design."),
            "headroom": bp.budget_headroom,
        }, status=409)

    if existing:
        existing.quantity = new_qty
        existing.save()
        stage = existing
    else:
        import random
        stage = StagedFurniture.objects.create(
            blueprint=bp, item=item, quantity=1,
            pin_x_pct=random.uniform(20, 80), pin_y_pct=random.uniform(35, 75),
            placed_by="manual", note="Added from catalog",
        )
    bp.recalc_spent(commit=True)
    return JsonResponse({
        "ok": True, "spent": float(bp.spent_inr), "headroom": bp.budget_headroom,
        "pin": {"pin_id": stage.pk, "sku": item.sku, "name": item.name,
                "category": item.category, "qty": stage.quantity,
                "unit_price": float(item.price_inr),
                "line_total": float(stage.line_total),
                "x": float(stage.pin_x_pct), "y": float(stage.pin_y_pct),
                "note": stage.note, "placed_by": stage.placed_by},
    })


@csrf_exempt
@require_POST
def remove_pin(request, pk: int):
    bp = get_object_or_404(EventBlueprint, pk=pk)
    body = _json_body(request)
    stage = get_object_or_404(StagedFurniture, pk=body.get("pin_id"), blueprint=bp)
    stage.delete()
    bp.recalc_spent(commit=True)
    return JsonResponse({"ok": True, "removed_pin_id": body.get("pin_id"),
                         "spent": float(bp.spent_inr), "headroom": bp.budget_headroom})


# ==================================================================== #
#  AI Copilot — natural language re-optimisation                       #
# ==================================================================== #
@csrf_exempt
@require_POST
def copilot(request):
    """Prompt bar re-runs the solver with nudges parsed from plain English:
        'raise budget to 80000', 'more lighting', 'fewer guests', 'theme royal'…
    """
    body = _json_body(request)
    bp = get_object_or_404(EventBlueprint, pk=body.get("blueprint_id"))
    prompt = (body.get("prompt") or "").lower()[:500]
    api_key = _resolve_api_key(request, body)
    changes = []

    m = re.search(r"(?:budget|spend)\D{0,6}([\d,]{3,12})", prompt)
    if m:
        val = float(m.group(1).replace(",", ""))
        if 1000 <= val <= 10_000_000:
            bp.budget_inr = val
            changes.append(f"budget → ₹{val:,.0f}")

    m = re.search(r"(\d{1,3})\s*(?:guests?|pax|people)", prompt)
    if m:
        bp.guest_count = max(min(int(m.group(1)), 400), 1)
        changes.append(f"guests → {bp.guest_count}")

    m = re.search(r"(?:room\s*)?(?:width|w)\D{0,4}(\d{1,3}(?:\.\d)?)(?:\s*(?:and|/)\s*depth\D{0,4}(\d{1,3}(?:\.\d)?))?", prompt)
    if m:
        bp.room_width_ft = float(m.group(1))
        changes.append(f"width → {m.group(1)} ft")
        if m.group(2):
            bp.room_depth_ft = float(m.group(2))
            changes.append(f"depth → {m.group(2)} ft")

    for t in EventTheme.objects.all():
        if t.code.replace("-", " ") in prompt or t.name.lower() in prompt or t.code in prompt:
            bp.theme = t
            changes.append(f"theme → {t.name}")
            break

    boost = None
    for cat in ("seating", "decor", "lighting", "hospitality"):
        if f"more {cat}" in prompt or f"heavier {cat}" in prompt or f"boost {cat}" in prompt:
            boost = cat
    if boost:
        th = bp.theme
        if boost == "lighting":
            th.decor_ratio = min(float(th.decor_ratio) + 0.10, 0.75)
            th.hospitality_ratio = max(float(th.hospitality_ratio) - 0.05, 0.05)
            th.seating_ratio = max(1 - float(th.decor_ratio) - float(th.hospitality_ratio), 0.05)
        else:
            setattr(th, f"{boost}_ratio", min(float(getattr(th, f"{boost}_ratio")) + 0.10, 0.8))
            th.seating_ratio = max(1 - float(th.decor_ratio) - float(th.hospitality_ratio), 0.05) \
                if boost != "seating" else float(th.seating_ratio)
            th.decor_ratio = max(1 - float(th.seating_ratio) - float(th.hospitality_ratio), 0.05) \
                if boost == "hospitality" else float(th.decor_ratio)
        changes.append(f"{boost} envelope +10%")

    reset = any(w in prompt for w in ("re-optimize", "reoptimize", "re-run", "fresh plan",
                                      "start over", "new plan"))
    if reset:
        StagedFurniture.objects.filter(blueprint=bp, placed_by="aura-engine").delete()
        changes.append("cleared engine pins")

    bp.save()
    plan = run_generation_pipeline(bp, api_key=api_key)
    plan["copilot_changes"] = changes or ["no recognised directives — plan refreshed"]
    plan["ok"] = True
    return JsonResponse(plan, safe=False)


# ==================================================================== #
#  Misc API                                                           #
# ==================================================================== #
@require_GET
def catalog_api(request):
    items = FurnitureItem.objects.filter(in_stock=True)
    return JsonResponse({"ok": True, "items": [
        {"id": i.pk, "sku": i.sku, "name": i.name, "category": i.category,
         "price": float(i.price_inr), "aura": i.aesthetic_score,
         "capacity": i.guest_capacity, "footprint": float(i.footprint_sqft),
         "blurb": i.blurb} for i in items]})


@csrf_exempt
@require_POST
def reseed(request):
    report = seed_aura_db(force=True)
    return JsonResponse({"ok": True, "report": report})
